"""
Summary and reporting utilities.

Contains:
- _print_full_summary(): Comprehensive summary after full suite
"""

from ..db import (
    get_pipeline_summary,
    get_stage_summary,
    get_cost_by_model,
    get_iteration_analysis,
    get_context_growth_analysis,
    get_streaming_analysis,
)


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
