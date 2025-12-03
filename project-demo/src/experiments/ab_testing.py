"""
A/B Testing experiment runner for prompt engineering analysis.

Enables systematic comparison of different prompt variants to understand
their impact on cost, quality, and latency.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from tqdm import tqdm

from ..config import (
    get_prompt,
    get_ab_test,
    ABTestConfig,
    VERBOSITY_QUERIES,
    DEFAULT_ITERATIONS,
    DELAY_BETWEEN_CALLS,
    DEFAULT_WORKERS,
    get_model_id,
)
from ..clients import call_model
from ..utils import calculate_cost, format_cost
from ..db import (
    init_db,
    log_run,
    log_stage,
    log_quality_score,
    log_ab_test,
    update_ab_test_status,
    get_ab_test_summary,
    get_ab_test_quality,
    get_ab_test_cost_quality_ratio,
)
from ..evaluation import evaluate_automated, evaluate_with_llm


@dataclass
class ABTestResult:
    """Result from a single A/B test iteration."""
    variant: str
    cost: float
    latency_ms: int
    input_tokens: int
    output_tokens: int
    output: str
    success: bool = True
    error_message: Optional[str] = None


def run_single_ab_iteration(
    prompt_template,
    variant: str,
    query: str,
    model: str,
    ab_test_name: str,
    use_llm_eval: bool = False,
) -> Optional[ABTestResult]:
    """Run a single iteration of an A/B test."""
    try:
        # Render the prompt with the specific variant
        prompt = prompt_template.render(variant=variant, query=query)
        
        # Call the model
        response = call_model(prompt, model)
        
        if not response.success:
            return ABTestResult(
                variant=variant,
                cost=0,
                latency_ms=0,
                input_tokens=0,
                output_tokens=0,
                output="",
                success=False,
                error_message=response.error_message,
            )
        
        # Calculate cost
        cost = calculate_cost(response.input_tokens, response.output_tokens, model)
        
        # Log to database
        run_id = log_run(
            workflow="ab_test",
            pipeline=f"ab_{prompt_template.name}",
            model=get_model_id(model),
            num_stages=1,
            total_input_tokens=response.input_tokens,
            total_output_tokens=response.output_tokens,
            total_cost=cost,
            total_latency_ms=response.latency_ms,
            final_output=response.text[:2000],
            success=True,
            pipeline_type="ab_test",
            prompt_variant=variant,
            ab_test_name=ab_test_name,
        )
        
        # Log stage
        log_stage(
            run_id=run_id,
            stage_order=1,
            stage_name="generation",
            stage_type="generation",
            model=get_model_id(model),
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=cost,
            latency_ms=response.latency_ms,
            prompt_variant=variant,
        )
        
        # Evaluate quality
        if use_llm_eval:
            quality = evaluate_with_llm(response.text, query)
        else:
            quality = evaluate_automated(response.text)
        
        log_quality_score(
            run_id=run_id,
            response_length=quality.response_length,
            word_count=quality.word_count,
            sentence_count=quality.sentence_count,
            avg_sentence_length=quality.avg_sentence_length,
            has_structure=quality.has_structure,
            vocabulary_richness=quality.vocabulary_richness,
            automated_score=quality.automated_score,
            relevance_score=quality.relevance_score,
            completeness_score=quality.completeness_score,
            clarity_score=quality.clarity_score,
            llm_score=quality.llm_score,
            combined_score=quality.combined_score,
            evaluation_cost=quality.llm_evaluation_cost,
        )
        
        return ABTestResult(
            variant=variant,
            cost=cost,
            latency_ms=response.latency_ms,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            output=response.text,
            success=True,
        )
        
    except Exception as e:
        return ABTestResult(
            variant=variant,
            cost=0,
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            output="",
            success=False,
            error_message=str(e),
        )


def run_ab_test(
    test_config: ABTestConfig,
    model: str = "flash",
    queries: Optional[List[str]] = None,
    iterations_per_variant: Optional[int] = None,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
    delay: float = DELAY_BETWEEN_CALLS,
    use_llm_eval: bool = False,
) -> Dict[str, List[ABTestResult]]:
    """
    Run an A/B test comparing different prompt variants.
    
    Args:
        test_config: A/B test configuration
        model: Model to use
        queries: List of test queries (defaults to VERBOSITY_QUERIES)
        iterations_per_variant: Override iterations from config
        parallel: Run in parallel
        workers: Number of parallel workers
        delay: Delay between sequential calls
        use_llm_eval: Use LLM for quality evaluation
    
    Returns:
        Dictionary mapping variant names to lists of results
    """
    init_db()
    
    queries = queries or VERBOSITY_QUERIES
    iterations = iterations_per_variant or test_config.iterations_per_variant
    
    print(f"\n{'='*60}")
    print(f"Running A/B Test: {test_config.name}")
    print(f"Prompt: {test_config.prompt_name}")
    print(f"Variants: {test_config.variants}")
    print(f"Model: {get_model_id(model)}")
    print(f"Iterations per variant: {iterations}")
    print(f"Parallel: {parallel}")
    print(f"{'='*60}\n")
    
    # Log the test
    log_ab_test(
        test_name=test_config.name,
        prompt_name=test_config.prompt_name,
        variants=test_config.variants,
        iterations_per_variant=iterations,
        description=test_config.description,
    )
    
    # Get the prompt template
    prompt_template = get_prompt(test_config.prompt_name)
    
    results: Dict[str, List[ABTestResult]] = {v: [] for v in test_config.variants}
    
    for variant in test_config.variants:
        print(f"\nVariant: {variant}")
        
        if parallel:
            # Build task list
            tasks = []
            for i in range(iterations):
                query = queries[i % len(queries)]
                tasks.append((prompt_template, variant, query, model, 
                            test_config.name, use_llm_eval))
            
            # Run in parallel
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(run_single_ab_iteration, *args): i 
                          for i, args in enumerate(tasks)}
                
                for future in tqdm(as_completed(futures), total=len(futures), 
                                  desc=f"  {variant}"):
                    try:
                        result = future.result()
                        if result and result.success:
                            results[variant].append(result)
                    except Exception as e:
                        print(f"\n  Warning: Task failed: {e}")
        else:
            # Sequential execution
            for i in tqdm(range(iterations), desc=f"  {variant}"):
                query = queries[i % len(queries)]
                result = run_single_ab_iteration(
                    prompt_template, variant, query, model,
                    test_config.name, use_llm_eval
                )
                if result and result.success:
                    results[variant].append(result)
                time.sleep(delay)
    
    # Update test status
    update_ab_test_status(test_config.name, "completed")
    
    # Print summary
    _print_ab_test_summary(test_config.name, results)
    
    return results


def run_ab_test_by_name(
    test_name: str,
    model: str = "flash",
    **kwargs,
) -> Dict[str, List[ABTestResult]]:
    """Run a pre-defined A/B test by name."""
    config = get_ab_test(test_name)
    return run_ab_test(config, model, **kwargs)


def run_custom_ab_test(
    prompt_name: str,
    variants: List[str],
    test_name: Optional[str] = None,
    model: str = "flash",
    iterations: int = 20,
    **kwargs,
) -> Dict[str, List[ABTestResult]]:
    """
    Run a custom A/B test with specified variants.
    
    Args:
        prompt_name: Name of the prompt template to test
        variants: List of variant names to compare
        test_name: Optional custom test name
        model: Model to use
        iterations: Iterations per variant
        **kwargs: Additional arguments for run_ab_test
    
    Returns:
        Dictionary of results by variant
    """
    config = ABTestConfig(
        name=test_name or f"custom_{prompt_name}_{int(time.time())}",
        prompt_name=prompt_name,
        variants=variants,
        iterations_per_variant=iterations,
        description=f"Custom A/B test for {prompt_name}",
    )
    return run_ab_test(config, model, **kwargs)


def _print_ab_test_summary(test_name: str, results: Dict[str, List[ABTestResult]]):
    """Print summary of A/B test results."""
    print(f"\n{'='*60}")
    print(f"A/B Test Complete: {test_name}")
    print(f"{'='*60}")
    
    print("\n--- Cost Summary ---")
    for variant, variant_results in results.items():
        if variant_results:
            costs = [r.cost for r in variant_results]
            avg_cost = sum(costs) / len(costs)
            print(f"  {variant}: avg={format_cost(avg_cost)}, n={len(costs)}")
    
    print("\n--- Latency Summary ---")
    for variant, variant_results in results.items():
        if variant_results:
            latencies = [r.latency_ms for r in variant_results]
            avg_latency = sum(latencies) / len(latencies)
            print(f"  {variant}: avg={avg_latency:.0f}ms")
    
    print("\n--- Output Length Summary ---")
    for variant, variant_results in results.items():
        if variant_results:
            lengths = [r.output_tokens for r in variant_results]
            avg_length = sum(lengths) / len(lengths)
            print(f"  {variant}: avg={avg_length:.0f} tokens")
    
    print("\nRun analysis notebook for detailed comparison and statistical tests.")


def print_ab_test_analysis(test_name: str):
    """Print detailed analysis of an A/B test from the database."""
    print(f"\n{'='*60}")
    print(f"A/B Test Analysis: {test_name}")
    print(f"{'='*60}")
    
    # Cost summary
    print("\n--- Cost by Variant ---")
    summary = get_ab_test_summary(test_name)
    if not summary.empty:
        print(summary.to_string(index=False))
    
    # Quality summary
    print("\n--- Quality by Variant ---")
    quality = get_ab_test_quality(test_name)
    if not quality.empty:
        print(quality.to_string(index=False))
    
    # Cost-quality ratio
    print("\n--- Cost-Quality Ratio (lower is better) ---")
    ratio = get_ab_test_cost_quality_ratio(test_name)
    if not ratio.empty:
        print(ratio.to_string(index=False))


def list_ab_tests() -> List[str]:
    """List available pre-defined A/B tests."""
    from ..config import PREDEFINED_AB_TESTS
    return list(PREDEFINED_AB_TESTS.keys())
