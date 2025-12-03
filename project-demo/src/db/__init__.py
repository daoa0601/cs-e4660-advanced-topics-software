"""
Database module for experiment tracking.

Provides:
- Thread-safe connection management with WAL mode
- Schema initialization and management
- Write operations (logging runs, stages, quality scores, A/B tests)
- Query operations (summaries, analysis, A/B test comparisons)
"""

from .connection import get_connection, get_lock, with_lock
from .schema import init_db, clear_all, get_table_info
from .write import (
    log_run,
    log_stage,
    log_quality_score,
    log_ab_test,
    update_ab_test_status,
)
from .query import (
    get_runs,
    get_stages,
    get_quality_scores,
    get_pipeline_summary,
    get_stage_summary,
    get_cost_by_model,
    get_cost_by_stage_type,
    get_iteration_analysis,
    get_context_growth_analysis,
    get_streaming_analysis,
    # A/B test queries
    get_ab_test_summary,
    get_ab_test_quality,
    get_ab_test_cost_quality_ratio,
    get_variant_comparison,
    get_ab_tests,
)

__all__ = [
    # Connection
    "get_connection",
    "get_lock",
    "with_lock",
    # Schema
    "init_db",
    "clear_all",
    "get_table_info",
    # Write
    "log_run",
    "log_stage",
    "log_quality_score",
    "log_ab_test",
    "update_ab_test_status",
    # Query
    "get_runs",
    "get_stages",
    "get_quality_scores",
    "get_pipeline_summary",
    "get_stage_summary",
    "get_cost_by_model",
    "get_cost_by_stage_type",
    "get_iteration_analysis",
    "get_context_growth_analysis",
    "get_streaming_analysis",
    # A/B test
    "get_ab_test_summary",
    "get_ab_test_quality",
    "get_ab_test_cost_quality_ratio",
    "get_variant_comparison",
    "get_ab_tests",
]
