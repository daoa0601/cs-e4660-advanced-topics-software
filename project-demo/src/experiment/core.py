"""
Core experiment infrastructure.

Contains:
- run_parallel_iterations(): Parallel task execution
- _run_single_iteration(): Generic single iteration runner
- run_workflow_experiment(): Main workflow orchestration
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable, List, Tuple, Any, Dict

from tqdm import tqdm

from ..logging_config import get_logger
from ..config import get_model_id
from ..cost_calculator import format_cost
from ..pipeline import PipelineResult

logger = get_logger(__name__)

# Default number of parallel workers (conservative to avoid API rate limits)
DEFAULT_WORKERS = 4


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
    from .logging import log_pipeline_result

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
            print(f"  Stages: {' -> '.join(s.name for s in pipeline.stages)}")
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


def _print_results_summary(workflow_name: str, results: dict):
    """Print summary of experiment results."""
    print(f"\n{'='*60}")
    print(f"{workflow_name} Experiment Complete")
    print(f"{'='*60}")

    for variant, costs in results.items():
        if costs:
            avg_cost = sum(costs) / len(costs)
            print(f"{variant}: avg cost = {format_cost(avg_cost)} (n={len(costs)})")
