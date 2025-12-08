"""
Experiment runner for LLM cost analysis.

Supports:
- Linear pipelines (standard multi-stage)
- Multi-model hybrid pipelines
- Agentic patterns (ReAct, multi-turn, self-correcting)
- Streaming with TTFT metrics
- Parallel execution for faster experimentation
"""

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable, List, Tuple, Any, Dict

from tqdm import tqdm

from .logging_config import setup_logging, get_logger

logger = get_logger(__name__)

from .config import (
    DEFAULT_ITERATIONS,
    DELAY_BETWEEN_CALLS,
    VERBOSITY_QUERIES,
    SHORT_CONTEXT,
    LONG_CONTEXT,
    TECHNICAL_DOCUMENTS,
    get_model_id,
)
from .clients import test_connection, test_streaming
from .cost_calculator import format_cost
from .pipeline import (
    get_pipeline,
    list_pipelines,
    Pipeline,
    ReActPipeline,
    MultiTurnPipeline,
    SelfCorrectingPipeline,
    PipelineResult,
    PIPELINES,
)
from .evaluator import evaluate_automated, evaluate_with_llm
from .db import (
    init_db,
    log_run,
    log_stage,
    log_quality_score,
    get_pipeline_summary,
    get_stage_summary,
    get_cost_by_stage_type,
    get_cost_by_model,
    get_iteration_analysis,
    get_context_growth_analysis,
    get_streaming_analysis,
)

# Default number of parallel workers (conservative to avoid API rate limits)
DEFAULT_WORKERS = 4


def log_pipeline_result(
    workflow: str,
    result: PipelineResult,
    model: str,
    query: str,
    pipeline_type: str = "linear",
    evaluate_quality: bool = True,
    use_llm_eval: bool = False,
) -> int:
    """Log a complete pipeline result to the database."""
    
    # Calculate average TTFT if available
    ttfts = [s.time_to_first_token_ms for s in result.stages if s.time_to_first_token_ms]
    avg_ttft = sum(ttfts) / len(ttfts) if ttfts else None
    
    # Serialize context tokens by turn
    context_tokens_json = json.dumps(result.context_tokens_by_turn) if result.context_tokens_by_turn else None
    
    # Log the main run
    run_id = log_run(
        workflow=workflow,
        pipeline=result.pipeline_name,
        pipeline_type=pipeline_type,
        model=get_model_id(model),
        num_stages=len(result.stages),
        total_input_tokens=result.total_input_tokens,
        total_output_tokens=result.total_output_tokens,
        total_cost=result.total_cost,
        total_latency_ms=result.total_latency_ms,
        final_output=result.final_output[:2000] if result.final_output else "",
        success=result.success,
        iterations=result.iterations,
        turns=result.turns,
        termination_reason=result.termination_reason.value if result.termination_reason else None,
        avg_ttft_ms=avg_ttft,
        context_tokens_by_turn=context_tokens_json,
    )
    
    # Log each stage
    for stage in result.stages:
        log_stage(
            run_id=run_id,
            stage_order=stage.stage_order,
            stage_name=stage.stage_name,
            stage_type=stage.stage_type.value,
            model=stage.model,
            input_tokens=stage.input_tokens,
            output_tokens=stage.output_tokens,
            cost=stage.cost,
            latency_ms=stage.latency_ms,
            success=stage.success,
            error_message=stage.error_message,
            iteration=stage.iteration,
            turn=stage.turn,
            time_to_first_token_ms=stage.time_to_first_token_ms,
            tokens_per_second=stage.tokens_per_second,
        )
    
    # Evaluate and log quality
    if evaluate_quality and result.success and result.final_output:
        if use_llm_eval:
            quality = evaluate_with_llm(result.final_output, query)
        else:
            quality = evaluate_automated(result.final_output)
        
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
    
    return run_id


def run_parallel_iterations(
    tasks: List[Tuple[Any, ...]],
    execute_fn: Callable,
    desc: str = "Running",
    workers: int = DEFAULT_WORKERS,
) -> List[Any]:
    """
    Run iterations in parallel using thread pool.

    Args:
        tasks: List of argument tuples for execute_fn
        execute_fn: Function to execute for each task
        desc: Description for progress bar
        workers: Number of parallel workers

    Returns:
        List of results (successful costs)
    """
    results = []
    logger.debug(f"Starting parallel execution: {len(tasks)} tasks, {workers} workers")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        futures = {executor.submit(execute_fn, *args): i for i, args in enumerate(tasks)}

        # Collect results with progress bar
        for future in tqdm(as_completed(futures), total=len(futures), desc=desc):
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Task failed: {e}")

    logger.debug(f"Parallel execution complete: {len(results)}/{len(tasks)} succeeded")
    return results


# =============================================================================
# Generic Experiment Infrastructure
# =============================================================================


def _run_single_iteration(
    pipeline,
    variant: str,
    query: str,
    model: str,
    streaming: bool,
    use_llm_eval: bool,
    workflow: str,
    pipeline_type: str,
) -> Optional[float]:
    """
    Generic single iteration runner for all workflow types.

    Args:
        pipeline: The pipeline instance to execute
        variant: Pipeline variant name (for logging)
        query: Input query/prompt
        model: Model identifier
        streaming: Use streaming API
        use_llm_eval: Use LLM evaluation
        workflow: Workflow name for database logging
        pipeline_type: Pipeline type for database logging

    Returns:
        Cost if successful, None otherwise
    """
    result = pipeline.execute(query, model, streaming=streaming)
    log_pipeline_result(
        workflow=workflow,
        result=result,
        model=model,
        query=query,
        pipeline_type=pipeline_type,
        use_llm_eval=use_llm_eval,
    )
    return result.total_cost if result.success else None


def run_workflow_experiment(
    workflow: str,
    pipeline_configs: Dict[str, tuple],
    model: str,
    iterations: int,
    delay: float,
    streaming: bool,
    use_llm_eval: bool,
    parallel: bool,
    workers: int,
    pipeline_type: str = "linear",
    experiment_name: Optional[str] = None,
) -> dict:
    """
    Generic experiment runner for all workflow types.

    Args:
        workflow: Workflow name (verbosity, context, react, etc.)
        pipeline_configs: Dict mapping variant name to (pipeline, queries_list)
        model: Model identifier
        iterations: Number of iterations per variant
        delay: Delay between sequential calls
        streaming: Use streaming API
        use_llm_eval: Use LLM evaluation
        parallel: Run iterations in parallel
        workers: Number of parallel workers
        pipeline_type: Pipeline type for logging
        experiment_name: Display name for the experiment

    Returns:
        Dict mapping variant names to lists of costs
    """
    from .cost_calculator import format_cost

    display_name = experiment_name or workflow.replace("_", " ").title()
    logger.info(f"Starting {display_name} experiment: model={get_model_id(model)}, iterations={iterations}")

    total_variants = len(pipeline_configs)
    total_iterations = iterations * total_variants

    print(f"\n{'='*60}")
    print(f"Running {display_name} Experiment")
    print(f"Model: {get_model_id(model)}")
    print(f"Iterations: {iterations} x {total_variants} variants = {total_iterations} total")
    print(f"Streaming: {streaming}")
    if parallel:
        print(f"Parallel: {workers} workers")
    print(f"{'='*60}\n")

    results = {variant: [] for variant in pipeline_configs}
    cumulative_cost = 0.0
    completed_iterations = 0
    start_time = time.time()

    for variant_idx, (variant, (pipeline, queries)) in enumerate(pipeline_configs.items()):
        # Print pipeline info
        print(f"\nPipeline: {variant} ({variant_idx + 1}/{total_variants})")
        if hasattr(pipeline, 'stages'):
            print(f"  Stages: {' → '.join(s.name for s in pipeline.stages)}")
        if hasattr(pipeline, 'max_iterations'):
            print(f"  Max iterations: {pipeline.max_iterations}")
        if hasattr(pipeline, 'max_retries'):
            print(f"  Max retries: {pipeline.max_retries}")

        if parallel:
            # Build task list for parallel execution
            tasks = [
                (pipeline, variant, queries[i % len(queries)], model,
                 streaming, use_llm_eval, workflow, pipeline_type)
                for i in range(iterations)
            ]
            costs = run_parallel_iterations(
                tasks, _run_single_iteration,
                desc=f"  {variant}", workers=workers
            )
            results[variant].extend(costs)
            variant_cost = sum(costs)
            cumulative_cost += variant_cost
            completed_iterations += iterations
        else:
            # Sequential execution with progress tracking
            variant_cost = 0.0
            for i in tqdm(range(iterations), desc=f"  {variant}"):
                query = queries[i % len(queries)]
                cost = _run_single_iteration(
                    pipeline, variant, query, model,
                    streaming, use_llm_eval, workflow, pipeline_type
                )
                if cost is not None:
                    results[variant].append(cost)
                    variant_cost += cost
                    cumulative_cost += cost
                completed_iterations += 1
                time.sleep(delay)

        # Print variant progress
        elapsed = time.time() - start_time
        remaining_iterations = total_iterations - completed_iterations
        if completed_iterations > 0:
            avg_time = elapsed / completed_iterations
            eta = avg_time * remaining_iterations
            print(f"  Variant cost: {format_cost(variant_cost)} | "
                  f"Cumulative: {format_cost(cumulative_cost)} | "
                  f"ETA: {eta/60:.1f}min")

    _print_results_summary(display_name, results)

    # Final progress summary
    total_time = time.time() - start_time
    print(f"\nExperiment completed in {total_time/60:.1f} minutes")
    print(f"Total cost: {format_cost(cumulative_cost)}")

    logger.info(f"Completed {display_name} experiment: cost={format_cost(cumulative_cost)}, time={total_time/60:.1f}min")
    return results


# =============================================================================
# Workflow-Specific Configurations
# =============================================================================


def run_verbosity_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the verbosity tax experiment (concise vs CoT vs hybrid)."""
    pipeline_configs = {
        "concise": (get_pipeline("verbosity_concise"), VERBOSITY_QUERIES),
        "cot": (get_pipeline("verbosity_cot"), VERBOSITY_QUERIES),
        "hybrid_cot": (get_pipeline("hybrid_cot"), VERBOSITY_QUERIES),
    }
    return run_workflow_experiment(
        workflow="verbosity",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="linear",
        experiment_name="Verbosity",
    )


def run_context_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the context length experiment."""
    pipeline_configs = {
        "short": (get_pipeline("context_short"), [SHORT_CONTEXT]),
        "long": (get_pipeline("context_long"), [LONG_CONTEXT]),
    }
    return run_workflow_experiment(
        workflow="context",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="linear",
        experiment_name="Context Length",
    )


def run_react_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the ReAct agent experiment."""
    research_queries = [
        "What are the main causes of climate change and what can be done about it?",
        "How does machine learning differ from traditional programming?",
        "What factors should I consider when choosing a programming language?",
        "What are the pros and cons of remote work?",
        "How do vaccines work to protect against diseases?",
    ]
    pipeline_configs = {
        "react": (get_pipeline("react_research"), research_queries),
        "react_hybrid": (get_pipeline("react_hybrid"), research_queries),
    }
    return run_workflow_experiment(
        workflow="react",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="react",
        experiment_name="ReAct Agent",
    )


def run_multiturn_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the multi-turn conversation experiment."""
    initial_queries = [
        "Tell me about renewable energy sources.",
        "Explain how neural networks learn.",
        "What is the history of the internet?",
        "How do electric vehicles work?",
        "Describe the water cycle.",
    ]
    pipeline_configs = {
        "3_turn": (get_pipeline("multiturn_3"), initial_queries),
        "5_turn": (get_pipeline("multiturn_5"), initial_queries),
    }
    result = run_workflow_experiment(
        workflow="multiturn",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="multiturn",
        experiment_name="Multi-Turn Conversation",
    )
    if result.get("5_turn"):
        print("\n  Context token growth tracked - see analysis notebook for details")
    return result


def run_self_correcting_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the self-correcting agent experiment."""
    coding_tasks = [
        "Write a Python function to check if a string is a palindrome.",
        "Create a SQL query to find the top 5 customers by total purchase amount.",
        "Write a regular expression to validate email addresses.",
        "Create a function to find the nth Fibonacci number efficiently.",
        "Write code to reverse a linked list.",
    ]
    pipeline_configs = {
        "self_correct": (get_pipeline("self_correcting"), coding_tasks),
        "self_correct_hybrid": (get_pipeline("self_correcting_hybrid"), coding_tasks),
    }
    return run_workflow_experiment(
        workflow="self_correcting",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="self_correcting",
        experiment_name="Self-Correcting Agent",
    )


def run_document_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run document analysis experiment with different pipeline strategies."""
    # Transform documents into query format
    doc_queries = [
        f"Document: {doc['title']}\nType: {doc['type']}\n\n{doc['content']}"
        for doc in TECHNICAL_DOCUMENTS
    ]
    pipeline_configs = {
        "doc_analysis_simple": (get_pipeline("doc_analysis_simple"), doc_queries),
        "doc_analysis_thorough": (get_pipeline("doc_analysis_thorough"), doc_queries),
        "doc_analysis_iterative": (get_pipeline("doc_analysis_iterative"), doc_queries),
        "doc_analysis_hybrid": (get_pipeline("doc_analysis_hybrid"), doc_queries),
    }
    return run_workflow_experiment(
        workflow="document",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="linear",
        experiment_name="Document Analysis",
    )


def run_rag_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run RAG pipeline experiment with different retrieval/verification strategies."""
    rag_queries = [
        "What is machine learning and how does it work?",
        "Explain the difference between deep learning and neural networks.",
        "How do transformers work in NLP?",
        "What are the ethical considerations in AI development?",
        "Describe reinforcement learning algorithms and their applications.",
    ]
    pipeline_configs = {
        "rag_basic": (get_pipeline("rag_basic"), rag_queries),
        "rag_verified": (get_pipeline("rag_verified"), rag_queries),
        "rag_hybrid": (get_pipeline("rag_hybrid"), rag_queries),
    }
    return run_workflow_experiment(
        workflow="rag",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="rag",
        experiment_name="RAG Pipeline",
    )


def _print_results_summary(workflow_name: str, results: dict):
    """Print summary of experiment results."""
    print(f"\n{'='*60}")
    print(f"{workflow_name} Experiment Complete")
    print(f"{'='*60}")
    
    for variant, costs in results.items():
        if costs:
            avg_cost = sum(costs) / len(costs)
            print(f"{variant}: avg cost = {format_cost(avg_cost)} (n={len(costs)})")


# =============================================================================
# Main Entry Points
# =============================================================================

def run_experiment(
    workflow: str,
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run an experiment by workflow name."""
    init_db()
    
    workflows = {
        "verbosity": run_verbosity_experiment,
        "context": run_context_experiment,
        "react": run_react_experiment,
        "multiturn": run_multiturn_experiment,
        "self_correcting": run_self_correcting_experiment,
        "document": run_document_experiment,
        "rag": run_rag_experiment,
    }
    
    if workflow not in workflows:
        raise ValueError(f"Unknown workflow: {workflow}. Available: {list(workflows.keys())}")
    
    return workflows[workflow](model, iterations, delay, streaming, use_llm_eval, parallel, workers)


def run_full_suite(
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
):
    """Run all experiments with both models."""
    print("\n" + "="*60)
    print("RUNNING FULL EXPERIMENT SUITE")
    print("="*60)
    
    print("\nTesting Vertex AI connection...")
    if not test_connection():
        print("Connection failed. Aborting.")
        return
    print("Connection successful!")
    
    if streaming:
        print("\nTesting streaming...")
        if not test_streaming():
            print("Streaming test failed. Continuing without streaming.")
            streaming = False
    
    # Run all workflows
    for workflow in ["verbosity", "context", "react", "multiturn", "self_correcting", "document", "rag"]:
        for model in ["flash", "pro"]:
            run_experiment(workflow, model, iterations, delay, streaming, use_llm_eval, parallel, workers)
    
    _print_full_summary()


def run_full_experiment():
    """
    Run the complete experiment package with optimal settings:
    - 20 iterations per variant
    - 16 parallel workers
    - Streaming enabled (with TTFT tracking)
    - LLM quality evaluation
    - Both Flash and Pro models
    - All workflows (verbosity, context, react, multiturn, self_correcting, document)
    - A/B testing for prompt variants
    """
    print("\n" + "="*70)
    print("🚀 RUNNING FULL EXPERIMENT PACKAGE")
    print("="*70)
    print("""
Configuration:
  • Iterations: 20 per variant
  • Workers: 16 (parallel execution)
  • Streaming: Enabled (TTFT metrics)
  • LLM Evaluation: Enabled (quality scoring)
  • Models: Flash + Pro
  • Workflows: All 6 workflows
  • A/B Tests: All pre-defined prompt tests
    """)
    
    # Full experiment settings
    FULL_ITERATIONS = 20
    FULL_WORKERS = 16
    
    # Test connection first
    print("Testing Vertex AI connection...")
    if not test_connection():
        print("❌ Connection failed. Aborting.")
        return
    print("✅ Connection successful!\n")
    
    # Test streaming
    print("Testing streaming API...")
    if not test_streaming():
        print("⚠️ Streaming test failed. Continuing without streaming metrics.")
        streaming = False
    else:
        print("✅ Streaming enabled!\n")
        streaming = True
    
    total_start = time.time()
    
    # =======================
    # Phase 1: Standard Workflows
    # =======================
    print("\n" + "="*70)
    print("PHASE 1: Standard Workflow Experiments")
    print("="*70)
    
    workflows = ["verbosity", "context", "react", "multiturn", "self_correcting", "document", "rag"]

    for workflow in workflows:
        for model in ["flash", "pro"]:
            run_experiment(
                workflow=workflow,
                model=model,
                iterations=FULL_ITERATIONS,
                delay=0.5,
                streaming=streaming,
                use_llm_eval=True,
                parallel=True,
                workers=FULL_WORKERS,
            )
    
    # =======================
    # Phase 2: A/B Testing
    # =======================
    print("\n" + "="*70)
    print("PHASE 2: A/B Testing Experiments")
    print("="*70)
    
    try:
        from .experiments import run_ab_test_by_name, list_ab_tests, print_ab_test_analysis
        
        ab_tests = list_ab_tests()
        print(f"\nRunning {len(ab_tests)} A/B tests: {ab_tests}\n")
        
        for test_name in ab_tests:
            for model in ["flash", "pro"]:
                print(f"\n--- A/B Test: {test_name} ({model}) ---")
                run_ab_test_by_name(
                    test_name,
                    model=model,
                    iterations_per_variant=FULL_ITERATIONS,
                    parallel=True,
                    workers=FULL_WORKERS,
                    use_llm_eval=True,
                )
        
        # Print A/B test summaries
        print("\n" + "="*70)
        print("A/B TEST RESULTS SUMMARY")
        print("="*70)
        
        for test_name in ab_tests:
            print_ab_test_analysis(test_name)
            
    except ImportError as e:
        print(f"⚠️ A/B testing module not available: {e}")
    except Exception as e:
        print(f"⚠️ A/B testing failed: {e}")
    
    # =======================
    # Final Summary
    # =======================
    total_time = time.time() - total_start
    
    print("\n" + "="*70)
    print("📊 FULL EXPERIMENT COMPLETE")
    print("="*70)
    print(f"\nTotal runtime: {total_time/60:.1f} minutes")
    
    _print_full_summary()
    
    print("\n" + "-"*70)
    print("Next steps:")
    print("  1. Open notebooks/analysis.ipynb for detailed analysis")
    print("  2. Review A/B test results for prompt optimization")
    print("  3. Compare cost-quality tradeoffs across pipelines")
    print("-"*70)


def _print_full_summary():
    """Print comprehensive summary after full suite."""
    print("\n" + "="*60)
    print("FULL SUITE COMPLETE")
    print("="*60)
    
    print("\n--- Pipeline Summary ---")
    print(get_pipeline_summary().to_string(index=False))
    
    print("\n--- Cost by Model ---")
    print(get_cost_by_model().to_string(index=False))
    
    print("\n--- Stage Type Summary ---")
    print(get_stage_summary().to_string(index=False))
    
    iteration_analysis = get_iteration_analysis()
    if not iteration_analysis.empty:
        print("\n--- Iteration Analysis (Agentic) ---")
        print(iteration_analysis.to_string(index=False))
    
    context_growth = get_context_growth_analysis()
    if not context_growth.empty:
        print("\n--- Context Growth (Multi-Turn) ---")
        print(context_growth.to_string(index=False))
    
    streaming_analysis = get_streaming_analysis()
    if not streaming_analysis.empty:
        print("\n--- Streaming Analysis (TTFT) ---")
        print(streaming_analysis.to_string(index=False))


# =============================================================================
# Health Check & Cost Estimation
# =============================================================================


def run_health_check() -> bool:
    """
    Check system health: database, API connectivity, and configuration.

    Returns:
        True if all checks pass, False otherwise
    """
    print("\n" + "="*60)
    print("System Health Check")
    print("="*60 + "\n")

    all_passed = True

    # 1. Check configuration
    print("1. Configuration")
    try:
        from .config import GCP_PROJECT_ID, GCP_REGION, DB_PATH
        if GCP_PROJECT_ID:
            print(f"   ✓ GCP_PROJECT_ID: {GCP_PROJECT_ID}")
        else:
            print("   ✗ GCP_PROJECT_ID: Not set")
            all_passed = False
        print(f"   ✓ GCP_REGION: {GCP_REGION}")
        print(f"   ✓ DB_PATH: {DB_PATH}")
    except Exception as e:
        print(f"   ✗ Configuration error: {e}")
        all_passed = False

    # 2. Check database
    print("\n2. Database")
    try:
        init_db()
        from .db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM runs")
        run_count = cursor.fetchone()[0]
        conn.close()
        print(f"   ✓ Database accessible ({run_count} existing runs)")
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        all_passed = False

    # 3. Check API connectivity
    print("\n3. API Connectivity")
    try:
        if test_connection():
            print("   ✓ Gemini API connection successful")
        else:
            print("   ✗ Gemini API connection failed")
            all_passed = False
    except Exception as e:
        print(f"   ✗ API error: {e}")
        all_passed = False

    # 4. Check streaming
    print("\n4. Streaming API")
    try:
        if test_streaming():
            print("   ✓ Streaming API functional")
        else:
            print("   ⚠ Streaming API unavailable (non-critical)")
    except Exception as e:
        print(f"   ⚠ Streaming check failed: {e} (non-critical)")

    # 5. Check pipelines
    print("\n5. Pipeline Registry")
    try:
        pipelines = list_pipelines()
        print(f"   ✓ {len(pipelines)} pipelines registered")
    except Exception as e:
        print(f"   ✗ Pipeline registry error: {e}")
        all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("Health Check: PASSED ✓")
    else:
        print("Health Check: FAILED ✗")
    print("="*60 + "\n")

    return all_passed


def estimate_experiment_cost(
    workflow: str,
    model: str,
    iterations: int,
) -> dict:
    """
    Estimate the cost of running an experiment before execution.

    Args:
        workflow: Workflow name
        model: Model identifier
        iterations: Number of iterations

    Returns:
        Dict with cost estimates
    """
    from .cost_calculator import calculate_cost, format_cost
    from .config import get_model_id

    # Estimated tokens per workflow (based on typical usage)
    WORKFLOW_ESTIMATES = {
        "verbosity": {
            "variants": 3,
            "avg_input_tokens": 500,
            "avg_output_tokens": 800,
        },
        "context": {
            "variants": 2,
            "avg_input_tokens": 2000,
            "avg_output_tokens": 500,
        },
        "react": {
            "variants": 2,
            "avg_input_tokens": 1500,
            "avg_output_tokens": 1200,
            "avg_iterations": 3,  # ReAct loops
        },
        "multiturn": {
            "variants": 2,
            "avg_input_tokens": 800,
            "avg_output_tokens": 600,
            "avg_turns": 4,  # Average turns
        },
        "self_correcting": {
            "variants": 2,
            "avg_input_tokens": 1000,
            "avg_output_tokens": 1500,
            "avg_retries": 2,
        },
        "document": {
            "variants": 4,
            "avg_input_tokens": 3000,
            "avg_output_tokens": 1000,
        },
    }

    if workflow not in WORKFLOW_ESTIMATES:
        return {"error": f"Unknown workflow: {workflow}"}

    est = WORKFLOW_ESTIMATES[workflow]
    variants = est["variants"]
    input_tokens = est["avg_input_tokens"]
    output_tokens = est["avg_output_tokens"]

    # Adjust for multi-step workflows
    multiplier = 1
    if "avg_iterations" in est:
        multiplier = est["avg_iterations"]
    elif "avg_turns" in est:
        multiplier = est["avg_turns"]
    elif "avg_retries" in est:
        multiplier = est["avg_retries"]

    # Calculate per-iteration cost
    per_iteration_cost = calculate_cost(
        input_tokens * multiplier,
        output_tokens * multiplier,
        model
    )

    # Total estimates
    total_iterations = iterations * variants
    total_cost = per_iteration_cost * total_iterations
    min_cost = total_cost * 0.7  # -30% variance
    max_cost = total_cost * 1.5  # +50% variance

    return {
        "workflow": workflow,
        "model": get_model_id(model),
        "iterations": iterations,
        "variants": variants,
        "total_api_calls": total_iterations,
        "estimated_cost": total_cost,
        "cost_range": (min_cost, max_cost),
        "per_iteration": per_iteration_cost,
    }


def print_cost_estimate(workflow: str, model: str, iterations: int):
    """Print formatted cost estimate."""
    from .cost_calculator import format_cost

    est = estimate_experiment_cost(workflow, model, iterations)

    if "error" in est:
        print(f"Error: {est['error']}")
        return

    print("\n" + "="*60)
    print("Cost Estimate")
    print("="*60)
    print(f"  Workflow:        {est['workflow']}")
    print(f"  Model:           {est['model']}")
    print(f"  Iterations:      {est['iterations']} x {est['variants']} variants")
    print(f"  Total API calls: {est['total_api_calls']}")
    print(f"  Per iteration:   {format_cost(est['per_iteration'])}")
    print("-"*60)
    print(f"  Estimated cost:  {format_cost(est['estimated_cost'])}")
    print(f"  Expected range:  {format_cost(est['cost_range'][0])} - {format_cost(est['cost_range'][1])}")
    print("="*60)
    print("\nNote: Actual costs may vary based on response length and complexity.")
    print("Use --llm-eval to add ~$0.01-0.05 per iteration for quality scoring.\n")


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run LLM cost experiments with multi-stage and agentic pipelines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 -m src.experiment --workflow verbosity --model flash --iterations 10
  python3 -m src.experiment --workflow react --model flash --iterations 5
  python3 -m src.experiment --workflow multiturn --model pro --streaming
  python3 -m src.experiment --full-suite --iterations 5
  python3 -m src.experiment --full-suite --parallel --workers 8
  python3 -m src.experiment --full-experiment  # Complete package: 20 iters, 16 workers, streaming, LLM eval, A/B tests
  python3 -m src.experiment --list-pipelines
        """
    )
    
    parser.add_argument(
        "--workflow",
        choices=["verbosity", "context", "react", "multiturn", "self_correcting", "document", "rag", "token_profile", "cost_quality"],
        help="Workflow to run (token_profile and cost_quality analyze existing data)"
    )
    parser.add_argument(
        "--model",
        choices=["flash", "pro"],
        help="Model to use"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Iterations per variant (default: {DEFAULT_ITERATIONS})"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DELAY_BETWEEN_CALLS,
        help=f"Delay between API calls (default: {DELAY_BETWEEN_CALLS}s)"
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use streaming API and capture TTFT metrics"
    )
    parser.add_argument(
        "--llm-eval",
        action="store_true",
        help="Use LLM for quality evaluation (costs extra)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run iterations in parallel (faster but ignores --delay)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Number of parallel workers (default: {DEFAULT_WORKERS})"
    )
    parser.add_argument(
        "--full-suite",
        action="store_true",
        help="Run all experiments with both models"
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test Vertex AI connection and exit"
    )
    parser.add_argument(
        "--test-streaming",
        action="store_true",
        help="Test streaming API and exit"
    )
    parser.add_argument(
        "--list-pipelines",
        action="store_true",
        help="List available pipelines and exit"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary of existing runs and exit"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear all existing data before running experiments"
    )
    parser.add_argument(
        "--full-experiment",
        action="store_true",
        help="Run complete experiment suite: all workflows, A/B tests, 20 iterations, 16 workers, streaming, LLM eval"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    parser.add_argument(
        "--estimate-cost",
        action="store_true",
        help="Estimate cost before running experiment (does not execute)"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Check system health (database, API, config) and exit"
    )

    args = parser.parse_args()

    # Configure logging based on CLI argument
    setup_logging(level=args.log_level)
    
    # Handle reset before init
    if args.reset:
        from .db import clear_all
        confirm = input("⚠️  This will delete ALL experiment data. Continue? [y/N]: ")
        if confirm.lower() == 'y':
            init_db()
            clear_all()
            print("Database reset complete.")
        else:
            print("Reset cancelled.")
            return
    
    init_db()
    
    if args.test_connection:
        print("Testing Vertex AI connection...")
        if test_connection():
            print("✓ Connection successful!")
        else:
            print("✗ Connection failed.")
        return
    
    if args.test_streaming:
        print("Testing streaming API...")
        if test_streaming():
            print("✓ Streaming successful!")
        else:
            print("✗ Streaming failed.")
        return
    
    if args.list_pipelines:
        print("\nAvailable Pipelines:")
        print("-" * 70)
        for p in list_pipelines():
            print(f"\n{p['name']} ({p['type']})")
            print(f"  Description: {p['description']}")
            if 'num_stages' in p:
                print(f"  Stages: {' → '.join(p['stages'])}")
            elif 'max_iterations' in p:
                print(f"  Max iterations: {p['max_iterations']}")
            elif 'num_turns' in p:
                print(f"  Turns: {p['num_turns']}")
            elif 'max_retries' in p:
                print(f"  Max retries: {p['max_retries']}")
            if p.get('multi_model'):
                print(f"  Multi-model: Yes")
        return
    
    if args.summary:
        _print_full_summary()
        return
    
    if args.health_check:
        success = run_health_check()
        return 0 if success else 1

    if args.full_suite:
        run_full_suite(args.iterations, args.delay, args.streaming, args.llm_eval, args.parallel, args.workers)
        return

    if args.full_experiment:
        run_full_experiment()
        return

    # Handle --estimate-cost (requires workflow and model)
    if args.estimate_cost:
        if not args.workflow or not args.model:
            parser.error("--estimate-cost requires both --workflow and --model")
        print_cost_estimate(args.workflow, args.model, args.iterations)
        return

    # Handle token_profile workflow (analysis only, doesn't require model)
    if args.workflow == "token_profile":
        from .experiments.token_profiler import run_token_profiler
        run_token_profiler(
            workflow=None,  # Analyze all workflows
            model=args.model,  # Optional model filter
            show_charts=True,
            save_charts=False,
        )
        return

    # Handle cost_quality workflow (analysis only, no API calls)
    if args.workflow == "cost_quality":
        from .experiments.cost_quality_analysis import run_cost_quality_analysis
        run_cost_quality_analysis(
            model=args.model,  # Optional model filter
            show_charts=True,
            save_charts=False,
        )
        return

    # Handle workflow execution (requires both workflow and model)
    if args.workflow or args.model:
        if not args.workflow:
            parser.error("--workflow is required when --model is specified")
        if not args.model:
            parser.error("--model is required when --workflow is specified")

        run_experiment(
            args.workflow, args.model, args.iterations,
            args.delay, args.streaming, args.llm_eval,
            args.parallel, args.workers
        )
        return

    # No action specified - show help
    parser.print_help()
    print("\n" + "-"*60)
    print("Quick start:")
    print("  python3 -m src.experiment --health-check")
    print("  python3 -m src.experiment --workflow verbosity --model flash --estimate-cost")
    print("  python3 -m src.experiment --workflow verbosity --model flash --iterations 5")
    print("-"*60)


if __name__ == "__main__":
    main()
