"""
CLI entry point for experiment runner.

Contains:
- main(): Command-line interface with argument parsing
"""

import argparse

from ..logging_config import setup_logging
from ..config import DEFAULT_ITERATIONS, DELAY_BETWEEN_CALLS
from ..clients import test_connection, test_streaming
from ..db import init_db
from ..pipeline import list_pipelines
from .core import DEFAULT_WORKERS
from .suite import run_experiment, run_full_suite, run_full_experiment
from .health import run_health_check, print_cost_estimate
from .summary import _print_full_summary


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
        help="Customizable full run: all workflows, both models (respects --iterations, --workers, etc.)"
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
        help="One-click production run: 20 iters, 16 workers, streaming, LLM eval, A/B tests (custom flags ignored)"
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
    parser.add_argument(
        "--session",
        type=str,
        metavar="NAME",
        help="Create or use a named session for isolated experiment data"
    )
    parser.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all experiment sessions and exit"
    )

    args = parser.parse_args()

    # Configure logging based on CLI argument
    setup_logging(level=args.log_level)

    # Handle session management (before other operations)
    if args.list_sessions:
        from ..session import list_sessions
        list_sessions()
        return

    if args.session:
        from ..session import new_session, use_session, get_current_session
        from pathlib import Path

        # Check if session exists
        from ..session import SESSION_DIR
        session_path = SESSION_DIR / args.session
        if session_path.exists():
            use_session(args.session)
        else:
            new_session(args.session)

        # Show current session
        session = get_current_session()
        print(f"\n📁 Using session: {session['name']}")

    # Handle reset before init
    if args.reset:
        from ..db import clear_all
        confirm = input("Warning: This will delete ALL experiment data. Continue? [y/N]: ")
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
            print("Connection successful!")
        else:
            print("Connection failed.")
        return

    if args.test_streaming:
        print("Testing streaming API...")
        if test_streaming():
            print("Streaming successful!")
        else:
            print("Streaming failed.")
        return

    if args.list_pipelines:
        print("\nAvailable Pipelines:")
        print("-" * 70)
        for p in list_pipelines():
            print(f"\n{p['name']} ({p['type']})")
            print(f"  Description: {p['description']}")
            if 'num_stages' in p:
                print(f"  Stages: {' -> '.join(p['stages'])}")
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
        from ..experiments.token_profiler import run_token_profiler
        run_token_profiler(
            workflow=None,  # Analyze all workflows
            model=args.model,  # Optional model filter
            show_charts=True,
            save_charts=False,
        )
        return

    # Handle cost_quality workflow (analysis only, no API calls)
    if args.workflow == "cost_quality":
        from ..experiments.cost_quality_analysis import run_cost_quality_analysis
        run_cost_quality_analysis(
            model=args.model,  # Optional model filter
            parallel=args.parallel,
            workers=args.workers,
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
