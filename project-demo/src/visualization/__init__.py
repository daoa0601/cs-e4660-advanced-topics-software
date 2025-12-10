"""
Visualization module for LLM Cost Decomposition experiments.

Provides centralized constants, data loading utilities, and chart factories
for consistent visualizations across notebooks and scripts.
"""

from .constants import (
    FLASH_COLOR,
    PRO_COLOR,
    MODEL_COLORS,
    DEFAULT_TEMPLATE,
    CHART_CONFIG,
)

from .data_loader import (
    load_experiment_data,
    load_runs_with_quality,
    clear_cache,
)

from .chart_factories import (
    create_cost_comparison_bar,
    create_cost_quality_scatter,
    create_model_comparison_bars,
    create_stage_distribution_chart,
    get_model_color_map,
    save_figure_png,
)

__all__ = [
    # Constants
    "FLASH_COLOR",
    "PRO_COLOR",
    "MODEL_COLORS",
    "DEFAULT_TEMPLATE",
    "CHART_CONFIG",
    # Data loading
    "load_experiment_data",
    "load_runs_with_quality",
    "clear_cache",
    # Chart factories
    "create_cost_comparison_bar",
    "create_cost_quality_scatter",
    "create_model_comparison_bars",
    "create_stage_distribution_chart",
    "get_model_color_map",
    "save_figure_png",
]
