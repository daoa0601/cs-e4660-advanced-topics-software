"""
Reusable chart factory functions for experiment visualizations.

Provides consistent chart creation with standardized styling,
reducing code duplication across notebooks and scripts.
"""

from typing import Optional, Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .constants import (
    MODEL_COLORS,
    FLASH_COLOR,
    PRO_COLOR,
    DEFAULT_TEMPLATE,
    CHART_CONFIG,
    STAGE_COLORS,
)


def get_model_color_map(data: pd.DataFrame, color_column: str = 'model') -> Dict[str, str]:
    """
    Generate a color map for models present in the data.

    Args:
        data: DataFrame containing model data
        color_column: Column name containing model identifiers

    Returns:
        Dictionary mapping model names to colors
    """
    if color_column not in data.columns:
        return {}

    unique_models = data[color_column].unique()
    return {model: MODEL_COLORS.get(model, '#888888') for model in unique_models}


def create_cost_comparison_bar(
    data: pd.DataFrame,
    x: str,
    y: str = 'total_cost',
    color: str = 'model',
    title: str = 'Cost Comparison',
    barmode: str = 'group',
    error_y: Optional[str] = None,
) -> go.Figure:
    """
    Create a bar chart comparing costs across categories.

    Args:
        data: DataFrame with cost data
        x: Column for x-axis (categories)
        y: Column for y-axis (cost values)
        color: Column for color grouping (typically 'model')
        title: Chart title
        barmode: 'group' or 'stack'
        error_y: Column for error bars (optional)

    Returns:
        Plotly Figure object
    """
    color_map = get_model_color_map(data, color)

    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        color_discrete_map=color_map,
        barmode=barmode,
        error_y=error_y,
        title=title,
        template=DEFAULT_TEMPLATE,
    )

    fig.update_layout(
        width=CHART_CONFIG['width'],
        height=CHART_CONFIG['height'],
        xaxis_title=x.replace('_', ' ').title(),
        yaxis_title=y.replace('_', ' ').title(),
    )

    return fig


def create_cost_quality_scatter(
    data: pd.DataFrame,
    x: str = 'total_cost',
    y: str = 'combined_score',
    color: str = 'model',
    size: Optional[str] = None,
    title: str = 'Cost vs Quality',
    hover_data: Optional[List[str]] = None,
) -> go.Figure:
    """
    Create a scatter plot showing cost vs quality relationship.

    Args:
        data: DataFrame with cost and quality data
        x: Column for x-axis (cost)
        y: Column for y-axis (quality score)
        color: Column for color grouping
        size: Column for marker size (optional)
        title: Chart title
        hover_data: Additional columns for hover info

    Returns:
        Plotly Figure object
    """
    color_map = get_model_color_map(data, color)

    fig = px.scatter(
        data,
        x=x,
        y=y,
        color=color,
        color_discrete_map=color_map,
        size=size,
        title=title,
        template=DEFAULT_TEMPLATE,
        hover_data=hover_data,
    )

    fig.update_layout(
        width=CHART_CONFIG['width'],
        height=CHART_CONFIG['height'],
        xaxis_title='Cost ($)',
        yaxis_title='Quality Score',
    )

    return fig


def create_model_comparison_bars(
    data: pd.DataFrame,
    metric: str,
    title: str = 'Model Comparison',
    show_values: bool = True,
) -> go.Figure:
    """
    Create a horizontal bar chart comparing models on a single metric.

    Args:
        data: DataFrame with model and metric columns
        metric: Column name of the metric to compare
        title: Chart title
        show_values: Whether to show values on bars

    Returns:
        Plotly Figure object
    """
    # Aggregate by model if needed
    if 'model' in data.columns:
        agg_data = data.groupby('model')[metric].mean().reset_index()
    else:
        agg_data = data

    fig = go.Figure()

    for _, row in agg_data.iterrows():
        model = row['model']
        value = row[metric]
        color = MODEL_COLORS.get(model, '#888888')

        fig.add_trace(go.Bar(
            x=[value],
            y=[model],
            orientation='h',
            marker_color=color,
            name=model,
            text=[f'{value:.4f}'] if show_values else None,
            textposition='auto',
        ))

    fig.update_layout(
        title=title,
        template=DEFAULT_TEMPLATE,
        width=CHART_CONFIG['width'],
        height=400,
        xaxis_title=metric.replace('_', ' ').title(),
        showlegend=False,
        barmode='group',
    )

    return fig


def create_stage_distribution_chart(
    stages_data: pd.DataFrame,
    value_col: str = 'cost',
    title: str = 'Cost Distribution by Stage',
) -> go.Figure:
    """
    Create a sunburst or bar chart showing cost distribution by stage type.

    Args:
        stages_data: DataFrame with stage-level data
        value_col: Column to sum for distribution (cost, tokens, etc.)
        title: Chart title

    Returns:
        Plotly Figure object
    """
    if stages_data.empty:
        return go.Figure()

    # Aggregate by stage type
    agg_data = stages_data.groupby('stage_type')[value_col].sum().reset_index()
    agg_data = agg_data.sort_values(value_col, ascending=True)

    # Map colors
    colors = [STAGE_COLORS.get(st, '#888888') for st in agg_data['stage_type']]

    fig = go.Figure(go.Bar(
        x=agg_data[value_col],
        y=agg_data['stage_type'],
        orientation='h',
        marker_color=colors,
        text=[f'${v:.4f}' if value_col == 'cost' else f'{v:,.0f}'
              for v in agg_data[value_col]],
        textposition='auto',
    ))

    fig.update_layout(
        title=title,
        template=DEFAULT_TEMPLATE,
        width=CHART_CONFIG['width'],
        height=max(400, len(agg_data) * 40),
        xaxis_title=value_col.replace('_', ' ').title(),
        yaxis_title='Stage Type',
    )

    return fig


def create_dual_panel_comparison(
    data: pd.DataFrame,
    metric1: str = 'total_cost',
    metric2: str = 'combined_score',
    group_by: str = 'pipeline',
    color_by: str = 'model',
    title: str = 'Cost vs Quality Comparison',
) -> go.Figure:
    """
    Create a dual-panel bar chart comparing two metrics side by side.

    Args:
        data: DataFrame with comparison data
        metric1: First metric (left panel)
        metric2: Second metric (right panel)
        group_by: Column to group bars by
        color_by: Column for color differentiation
        title: Chart title

    Returns:
        Plotly Figure object
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            metric1.replace('_', ' ').title(),
            metric2.replace('_', ' ').title()
        ),
    )

    # Aggregate data
    agg_data = data.groupby([group_by, color_by]).agg({
        metric1: 'mean',
        metric2: 'mean',
    }).reset_index()

    for model in agg_data[color_by].unique():
        model_data = agg_data[agg_data[color_by] == model]
        color = MODEL_COLORS.get(model, '#888888')

        # Left panel - metric1
        fig.add_trace(
            go.Bar(
                x=model_data[group_by],
                y=model_data[metric1],
                name=model,
                marker_color=color,
                legendgroup=model,
            ),
            row=1, col=1
        )

        # Right panel - metric2
        fig.add_trace(
            go.Bar(
                x=model_data[group_by],
                y=model_data[metric2],
                name=model,
                marker_color=color,
                legendgroup=model,
                showlegend=False,
            ),
            row=1, col=2
        )

    fig.update_layout(
        title=title,
        template=DEFAULT_TEMPLATE,
        width=CHART_CONFIG['width'],
        height=CHART_CONFIG['height'],
        barmode='group',
    )

    return fig
