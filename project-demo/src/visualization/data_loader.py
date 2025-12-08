"""
Unified data loading utilities with caching for visualization.

Provides consistent data loading and merging patterns across all
visualization scripts and notebooks.
"""

from functools import lru_cache
from typing import Tuple, Optional
import pandas as pd

from src.db.query import get_runs, get_stages, get_quality_scores


@lru_cache(maxsize=1)
def load_experiment_data(success_only: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and merge experiment data with caching.

    Returns a tuple of (merged_runs_quality, stages) DataFrames.
    The runs DataFrame is merged with quality scores on run_id.

    Args:
        success_only: If True, only load successful runs

    Returns:
        Tuple of (merged_data, stages_data) DataFrames
    """
    runs_df = get_runs(success_only=success_only)
    stages_df = get_stages()
    quality_df = get_quality_scores()

    # Merge runs with quality scores
    if not quality_df.empty and not runs_df.empty:
        # Handle both column naming conventions
        if 'run_id' in quality_df.columns:
            merged = runs_df.merge(
                quality_df,
                left_on='id',
                right_on='run_id',
                how='left',
                suffixes=('', '_quality')
            )
        else:
            merged = runs_df.merge(
                quality_df,
                on='id',
                how='left',
                suffixes=('', '_quality')
            )
    else:
        merged = runs_df

    return merged, stages_df


def load_runs_with_quality(
    workflow: Optional[str] = None,
    model: Optional[str] = None,
    success_only: bool = True,
) -> pd.DataFrame:
    """
    Load runs merged with quality scores, with optional filtering.

    Args:
        workflow: Filter by workflow name
        model: Filter by model name
        success_only: If True, only load successful runs

    Returns:
        DataFrame with runs and quality metrics merged
    """
    runs_df = get_runs(
        workflow=workflow,
        model=model,
        success_only=success_only,
    )
    quality_df = get_quality_scores()

    if not quality_df.empty and not runs_df.empty:
        if 'run_id' in quality_df.columns:
            merged = runs_df.merge(
                quality_df,
                left_on='id',
                right_on='run_id',
                how='left',
                suffixes=('', '_quality')
            )
        else:
            merged = runs_df.merge(
                quality_df,
                on='id',
                how='left',
                suffixes=('', '_quality')
            )
        return merged

    return runs_df


def clear_cache():
    """Clear the data loading cache to force fresh data reload."""
    load_experiment_data.cache_clear()


def get_model_display_name(model: str) -> str:
    """Convert model identifier to display-friendly name."""
    name_map = {
        'gemini-2.5-flash': 'Flash',
        'gemini-2.5-pro': 'Pro',
        'flash': 'Flash',
        'pro': 'Pro',
    }
    return name_map.get(model, model)


def calculate_summary_stats(data: pd.DataFrame, group_by: str = 'model') -> pd.DataFrame:
    """
    Calculate standard summary statistics grouped by a column.

    Args:
        data: DataFrame with experiment data
        group_by: Column to group by (default: 'model')

    Returns:
        DataFrame with summary statistics
    """
    if data.empty:
        return pd.DataFrame()

    numeric_cols = ['total_cost', 'total_latency_ms', 'total_input_tokens',
                    'total_output_tokens', 'combined_score']

    available_cols = [c for c in numeric_cols if c in data.columns]

    stats = data.groupby(group_by)[available_cols].agg(['mean', 'std', 'min', 'max', 'count'])
    return stats
