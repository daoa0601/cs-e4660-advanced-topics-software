"""
Experiment runner for LLM cost analysis.

Supports:
- Linear pipelines (standard multi-stage)
- Multi-model hybrid pipelines
- Agentic patterns (ReAct, multi-turn, self-correcting)
- RAG pipelines with real embedding retrieval
- Streaming with TTFT metrics
- Parallel execution for faster experimentation
"""

# Core infrastructure
from .core import (
    run_parallel_iterations,
    run_workflow_experiment,
    DEFAULT_WORKERS,
)

# Logging
from .logging import log_pipeline_result

# Workflow experiments
from .workflows import (
    run_verbosity_experiment,
    run_context_experiment,
    run_react_experiment,
    run_multiturn_experiment,
    run_self_correcting_experiment,
    run_document_experiment,
    run_rag_experiment,
)

# Suite runners
from .suite import (
    run_experiment,
    run_full_suite,
    run_full_experiment,
)

# Health and estimation
from .health import (
    run_health_check,
    estimate_experiment_cost,
    print_cost_estimate,
)

# CLI
from .cli import main

# Summary
from .summary import _print_full_summary

__all__ = [
    # Core
    "run_parallel_iterations",
    "run_workflow_experiment",
    "DEFAULT_WORKERS",
    # Logging
    "log_pipeline_result",
    # Workflows
    "run_verbosity_experiment",
    "run_context_experiment",
    "run_react_experiment",
    "run_multiturn_experiment",
    "run_self_correcting_experiment",
    "run_document_experiment",
    "run_rag_experiment",
    # Suite
    "run_experiment",
    "run_full_suite",
    "run_full_experiment",
    # Health
    "run_health_check",
    "estimate_experiment_cost",
    "print_cost_estimate",
    # CLI
    "main",
    # Summary
    "_print_full_summary",
]
