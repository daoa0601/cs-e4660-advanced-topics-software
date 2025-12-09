"""
Experiment suite runners.

Contains:
- run_experiment(): Single workflow dispatcher
- run_full_suite(): All workflows for both models
- run_full_experiment(): Complete package with phases & A/B testing
"""

import time

from ..config import DEFAULT_ITERATIONS, DELAY_BETWEEN_CALLS
from ..clients import test_connection, test_streaming
from ..db import init_db
from .core import DEFAULT_WORKERS
from .workflows import (
    run_verbosity_experiment,
    run_context_experiment,
    run_react_experiment,
    run_multiturn_experiment,
    run_self_correcting_experiment,
    run_document_experiment,
    run_rag_experiment,
)
from .summary import _print_full_summary


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
    print("RUNNING FULL EXPERIMENT PACKAGE")
    print("="*70)
    print("""
Configuration:
  - Iterations: 20 per variant
  - Workers: 16 (parallel execution)
  - Streaming: Enabled (TTFT metrics)
  - LLM Evaluation: Enabled (quality scoring)
  - Models: Flash + Pro
  - Workflows: All 6 workflows
  - A/B Tests: All pre-defined prompt tests
    """)

    # Full experiment settings
    FULL_ITERATIONS = 20
    FULL_WORKERS = 16

    # Test connection first
    print("Testing Vertex AI connection...")
    if not test_connection():
        print("Connection failed. Aborting.")
        return
    print("Connection successful!\n")

    # Test streaming
    print("Testing streaming API...")
    if not test_streaming():
        print("Streaming test failed. Continuing without streaming metrics.")
        streaming = False
    else:
        print("Streaming enabled!\n")
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
        from ..experiments import run_ab_test_by_name, list_ab_tests, print_ab_test_analysis

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
        print(f"A/B testing module not available: {e}")
    except Exception as e:
        print(f"A/B testing failed: {e}")

    # =======================
    # Final Summary
    # =======================
    total_time = time.time() - total_start

    print("\n" + "="*70)
    print("FULL EXPERIMENT COMPLETE")
    print("="*70)
    print(f"\nTotal runtime: {total_time/60:.1f} minutes")

    _print_full_summary()

    print("\n" + "-"*70)
    print("Next steps:")
    print("  1. Open notebooks/analysis.ipynb for detailed analysis")
    print("  2. Review A/B test results for prompt optimization")
    print("  3. Compare cost-quality tradeoffs across pipelines")
    print("-"*70)
