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
from typing import Optional, Callable, List, Tuple, Any

from tqdm import tqdm

from .config import (
    DEFAULT_ITERATIONS,
    DELAY_BETWEEN_CALLS,
    VERBOSITY_QUERIES,
    SHORT_CONTEXT,
    LONG_CONTEXT,
    TECHNICAL_DOCUMENTS,
    get_model_id,
)
from .vertex_client import test_connection, test_streaming
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
                print(f"\n  Warning: Task failed: {e}")
    
    return results


# =============================================================================
# Workflow Runners
# =============================================================================

def _run_single_verbosity_iteration(
    pipeline, variant, model, query, streaming, use_llm_eval
) -> Optional[float]:
    """Execute a single verbosity iteration (for parallel execution)."""
    result = pipeline.execute(query, model, streaming=streaming)
    
    log_pipeline_result(
        workflow="verbosity",
        result=result,
        model=model,
        query=query,
        pipeline_type="linear",
        use_llm_eval=use_llm_eval,
    )
    
    return result.total_cost if result.success else None


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
    print(f"\n{'='*60}")
    print(f"Running Verbosity Experiment")
    print(f"Model: {get_model_id(model)}")
    print(f"Iterations: {iterations}")
    print(f"Streaming: {streaming}")
    print(f"Parallel: {parallel} (workers: {workers})" if parallel else "")
    print(f"{'='*60}\n")
    
    results = {"concise": [], "cot": [], "hybrid_cot": []}
    
    pipelines = {
        "concise": get_pipeline("verbosity_concise"),
        "cot": get_pipeline("verbosity_cot"),
        "hybrid_cot": get_pipeline("hybrid_cot"),
    }
    
    for variant, pipeline in pipelines.items():
        print(f"\nPipeline: {variant}")
        if isinstance(pipeline, Pipeline):
            print(f"  Stages: {' → '.join(s.name for s in pipeline.stages)}")
            if any(s.model_override for s in pipeline.stages):
                models_used = [s.model_override or model for s in pipeline.stages]
                print(f"  Models: {' → '.join(models_used)}")
        
        if parallel:
            # Build task list
            tasks = [
                (pipeline, variant, model, VERBOSITY_QUERIES[i % len(VERBOSITY_QUERIES)], 
                 streaming, use_llm_eval)
                for i in range(iterations)
            ]
            costs = run_parallel_iterations(
                tasks, _run_single_verbosity_iteration, 
                desc=f"  {variant}", workers=workers
            )
            results[variant].extend(costs)
        else:
            # Sequential execution
            for i in tqdm(range(iterations), desc=f"  {variant}"):
                query = VERBOSITY_QUERIES[i % len(VERBOSITY_QUERIES)]
                
                result = pipeline.execute(query, model, streaming=streaming)
                
                log_pipeline_result(
                    workflow="verbosity",
                    result=result,
                    model=model,
                    query=query,
                    pipeline_type="linear",
                    use_llm_eval=use_llm_eval,
                )
                
                if result.success:
                    results[variant].append(result.total_cost)
                
                time.sleep(delay)
    
    _print_results_summary("Verbosity", results)
    return results


def _run_single_context_iteration(
    pipeline, variant, context, model, streaming, use_llm_eval
) -> Optional[float]:
    """Execute a single context iteration."""
    result = pipeline.execute(context, model, streaming=streaming)
    log_pipeline_result(
        workflow="context",
        result=result,
        model=model,
        query=f"Summarize: {context[:100]}...",
        pipeline_type="linear",
        use_llm_eval=use_llm_eval,
    )
    return result.total_cost if result.success else None


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
    print(f"\n{'='*60}")
    print(f"Running Context Length Experiment")
    print(f"Model: {get_model_id(model)}")
    print(f"Parallel: {parallel}" if parallel else "")
    print(f"{'='*60}\n")
    
    results = {"short": [], "long": []}
    
    pipelines = {
        "short": get_pipeline("context_short"),
        "long": get_pipeline("context_long"),
    }
    
    contexts = {
        "short": SHORT_CONTEXT,
        "long": LONG_CONTEXT,
    }
    
    for variant in ["short", "long"]:
        pipeline = pipelines[variant]
        context = contexts[variant]
        
        print(f"\nPipeline: {variant} ({len(pipeline.stages)} stages)")
        
        if parallel:
            tasks = [(pipeline, variant, context, model, streaming, use_llm_eval)
                     for _ in range(iterations)]
            costs = run_parallel_iterations(
                tasks, _run_single_context_iteration,
                desc=f"  {variant}", workers=workers
            )
            results[variant].extend(costs)
        else:
            for i in tqdm(range(iterations), desc=f"  {variant}"):
                result = pipeline.execute(context, model, streaming=streaming)
                log_pipeline_result(
                    workflow="context",
                    result=result,
                    model=model,
                    query=f"Summarize: {context[:100]}...",
                    pipeline_type="linear",
                    use_llm_eval=use_llm_eval,
                )
                if result.success:
                    results[variant].append(result.total_cost)
                time.sleep(delay)
    
    _print_results_summary("Context", results)
    return results


def _run_single_react_iteration(
    pipeline, variant, query, model, streaming, use_llm_eval
) -> Optional[float]:
    """Execute a single ReAct iteration."""
    result = pipeline.execute(query, model, streaming=streaming)
    log_pipeline_result(
        workflow="react",
        result=result,
        model=model,
        query=query,
        pipeline_type="react",
        use_llm_eval=use_llm_eval,
    )
    return result.total_cost if result.success else None


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
    print(f"\n{'='*60}")
    print(f"Running ReAct Agent Experiment")
    print(f"Model: {get_model_id(model)}")
    print(f"Parallel: {parallel}" if parallel else "")
    print(f"{'='*60}\n")
    
    results = {"react": [], "react_hybrid": []}
    
    research_queries = [
        "What are the main causes of climate change and what can be done about it?",
        "How does machine learning differ from traditional programming?",
        "What factors should I consider when choosing a programming language?",
        "What are the pros and cons of remote work?",
        "How do vaccines work to protect against diseases?",
    ]
    
    pipelines = {
        "react": get_pipeline("react_research"),
        "react_hybrid": get_pipeline("react_hybrid"),
    }
    
    for variant, pipeline in pipelines.items():
        print(f"\nPipeline: {variant}")
        print(f"  Max iterations: {pipeline.max_iterations}")
        print(f"  Think model: {pipeline.think_model}, Act model: {pipeline.act_model}")
        
        if parallel:
            tasks = [(pipeline, variant, research_queries[i % len(research_queries)],
                     model, streaming, use_llm_eval) for i in range(iterations)]
            costs = run_parallel_iterations(
                tasks, _run_single_react_iteration,
                desc=f"  {variant}", workers=workers
            )
            results[variant].extend(costs)
        else:
            for i in tqdm(range(iterations), desc=f"  {variant}"):
                query = research_queries[i % len(research_queries)]
                result = pipeline.execute(query, model, streaming=streaming)
                log_pipeline_result(
                    workflow="react",
                    result=result,
                    model=model,
                    query=query,
                    pipeline_type="react",
                    use_llm_eval=use_llm_eval,
                )
                if result.success:
                    results[variant].append(result.total_cost)
                time.sleep(delay)
    
    _print_results_summary("ReAct", results)
    return results


def _run_single_multiturn_iteration(
    pipeline, variant, query, model, streaming, use_llm_eval
) -> Optional[float]:
    """Execute a single multi-turn iteration."""
    result = pipeline.execute(query, model, streaming=streaming)
    log_pipeline_result(
        workflow="multiturn",
        result=result,
        model=model,
        query=query,
        pipeline_type="multiturn",
        use_llm_eval=use_llm_eval,
    )
    return result.total_cost if result.success else None


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
    print(f"\n{'='*60}")
    print(f"Running Multi-Turn Conversation Experiment")
    print(f"Model: {get_model_id(model)}")
    print(f"Parallel: {parallel}" if parallel else "")
    print(f"{'='*60}\n")
    
    results = {"3_turn": [], "5_turn": []}
    
    initial_queries = [
        "Tell me about renewable energy sources.",
        "Explain how neural networks learn.",
        "What is the history of the internet?",
        "How do electric vehicles work?",
        "Describe the water cycle.",
    ]
    
    pipelines = {
        "3_turn": get_pipeline("multiturn_3"),
        "5_turn": get_pipeline("multiturn_5"),
    }
    
    for variant, pipeline in pipelines.items():
        num_turns = len(pipeline.turns) + 1
        print(f"\nPipeline: {variant} ({num_turns} turns)")
        
        if parallel:
            tasks = [(pipeline, variant, initial_queries[i % len(initial_queries)],
                     model, streaming, use_llm_eval) for i in range(iterations)]
            costs = run_parallel_iterations(
                tasks, _run_single_multiturn_iteration,
                desc=f"  {variant}", workers=workers
            )
            results[variant].extend(costs)
        else:
            for i in tqdm(range(iterations), desc=f"  {variant}"):
                query = initial_queries[i % len(initial_queries)]
                result = pipeline.execute(query, model, streaming=streaming)
                log_pipeline_result(
                    workflow="multiturn",
                    result=result,
                    model=model,
                    query=query,
                    pipeline_type="multiturn",
                    use_llm_eval=use_llm_eval,
                )
                if result.success:
                    results[variant].append(result.total_cost)
                time.sleep(delay)
    
    _print_results_summary("Multi-Turn", results)
    
    if results["5_turn"]:
        print("\n  Context token growth tracked - see analysis notebook for details")
    
    return results


def _run_single_self_correcting_iteration(
    pipeline, variant, task, model, streaming, use_llm_eval
) -> Optional[float]:
    """Execute a single self-correcting iteration."""
    result = pipeline.execute(task, model, streaming=streaming)
    log_pipeline_result(
        workflow="self_correcting",
        result=result,
        model=model,
        query=task,
        pipeline_type="self_correcting",
        use_llm_eval=use_llm_eval,
    )
    return result.total_cost if result.success else None


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
    print(f"\n{'='*60}")
    print(f"Running Self-Correcting Agent Experiment")
    print(f"Model: {get_model_id(model)}")
    print(f"Parallel: {parallel}" if parallel else "")
    print(f"{'='*60}\n")
    
    results = {"self_correct": [], "self_correct_hybrid": []}
    
    tasks = [
        "Write a Python function to check if a string is a palindrome.",
        "Create a SQL query to find the top 5 customers by total purchase amount.",
        "Write a regular expression to validate email addresses.",
        "Create a function to find the nth Fibonacci number efficiently.",
        "Write code to reverse a linked list.",
    ]
    
    pipelines = {
        "self_correct": get_pipeline("self_correcting"),
        "self_correct_hybrid": get_pipeline("self_correcting_hybrid"),
    }
    
    for variant, pipeline in pipelines.items():
        print(f"\nPipeline: {variant}")
        print(f"  Max retries: {pipeline.max_retries}")
        print(f"  Generate: {pipeline.generate_model}, Validate: {pipeline.validate_model}")
        
        if parallel:
            task_list = [(pipeline, variant, tasks[i % len(tasks)],
                         model, streaming, use_llm_eval) for i in range(iterations)]
            costs = run_parallel_iterations(
                task_list, _run_single_self_correcting_iteration,
                desc=f"  {variant}", workers=workers
            )
            results[variant].extend(costs)
        else:
            for i in tqdm(range(iterations), desc=f"  {variant}"):
                task = tasks[i % len(tasks)]
                result = pipeline.execute(task, model, streaming=streaming)
                log_pipeline_result(
                    workflow="self_correcting",
                    result=result,
                    model=model,
                    query=task,
                    pipeline_type="self_correcting",
                    use_llm_eval=use_llm_eval,
                )
                if result.success:
                    results[variant].append(result.total_cost)
                time.sleep(delay)
    
    _print_results_summary("Self-Correcting", results)
    return results


def _run_single_document_iteration(
    pipeline, pipeline_name, doc, model, streaming, use_llm_eval
) -> Optional[float]:
    """Execute a single document analysis iteration."""
    doc_input = f"Document: {doc['title']}\nType: {doc['type']}\n\n{doc['content']}"
    result = pipeline.execute(doc_input, model, streaming=streaming)
    log_pipeline_result(
        workflow="document",
        result=result,
        model=model,
        query=f"Analyze: {doc['title']}",
        pipeline_type="linear",
        use_llm_eval=use_llm_eval,
    )
    return result.total_cost if result.success else None


def run_document_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """
    Run document analysis experiment.
    
    Tests different pipeline strategies for analyzing technical documents.
    """
    print(f"\n{'='*60}")
    print(f"Running Document Analysis Experiment")
    print(f"Model: {get_model_id(model)}")
    print(f"Iterations: {iterations}")
    print(f"Documents: {len(TECHNICAL_DOCUMENTS)}")
    print(f"Parallel: {parallel}" if parallel else "")
    print(f"{'='*60}\n")
    
    results = {
        "doc_analysis_simple": [],
        "doc_analysis_thorough": [],
        "doc_analysis_iterative": [],
        "doc_analysis_hybrid": [],
    }
    
    pipelines_to_run = [
        "doc_analysis_simple",
        "doc_analysis_thorough", 
        "doc_analysis_iterative",
        "doc_analysis_hybrid",
    ]
    
    for pipeline_name in pipelines_to_run:
        pipeline = get_pipeline(pipeline_name)
        print(f"\nPipeline: {pipeline_name} ({len(pipeline.stages)} stages)")
        print(f"  Stages: {' → '.join(s.name for s in pipeline.stages)}")
        
        if parallel:
            tasks = [(pipeline, pipeline_name, 
                     TECHNICAL_DOCUMENTS[i % len(TECHNICAL_DOCUMENTS)],
                     model, streaming, use_llm_eval) for i in range(iterations)]
            costs = run_parallel_iterations(
                tasks, _run_single_document_iteration,
                desc=f"  {pipeline_name}", workers=workers
            )
            results[pipeline_name].extend(costs)
        else:
            for i in tqdm(range(iterations), desc=f"  {pipeline_name}"):
                doc = TECHNICAL_DOCUMENTS[i % len(TECHNICAL_DOCUMENTS)]
                doc_input = f"Document: {doc['title']}\nType: {doc['type']}\n\n{doc['content']}"
                result = pipeline.execute(doc_input, model, streaming=streaming)
                log_pipeline_result(
                    workflow="document",
                    result=result,
                    model=model,
                    query=f"Analyze: {doc['title']}",
                    pipeline_type="linear",
                    use_llm_eval=use_llm_eval,
                )
                if result.success:
                    results[pipeline_name].append(result.total_cost)
                time.sleep(delay)
    
    _print_results_summary("Document Analysis", results)
    return results


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
    for workflow in ["verbosity", "context", "react", "multiturn", "self_correcting", "document"]:
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
    
    workflows = ["verbosity", "context", "react", "multiturn", "self_correcting", "document"]
    
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
        choices=["verbosity", "context", "react", "multiturn", "self_correcting", "document"],
        help="Workflow to run"
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
    
    args = parser.parse_args()
    
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
    
    if args.full_suite:
        run_full_suite(args.iterations, args.delay, args.streaming, args.llm_eval, args.parallel, args.workers)
        return
    
    if args.full_experiment:
        run_full_experiment()
        return
    
    if args.workflow and args.model:
        run_experiment(
            args.workflow, args.model, args.iterations, 
            args.delay, args.streaming, args.llm_eval,
            args.parallel, args.workers
        )
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
