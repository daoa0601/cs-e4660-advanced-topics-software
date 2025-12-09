"""
Cost-Quality Frontier Analysis

Analyzes the Pareto frontier of cost vs quality to identify optimal
pipeline configurations and cost-effectiveness rankings.

Usage:
    python3 -m src.experiments.cost_quality_analysis
    python3 -m src.experiment --workflow cost_quality
"""

import argparse
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from tqdm import tqdm

from src.db import get_runs, get_stages, get_quality_scores
from src.visualization import (
    FLASH_COLOR,
    PRO_COLOR,
    MODEL_COLORS,
    DEFAULT_TEMPLATE,
    CHART_CONFIG,
    load_experiment_data,
)


@dataclass
class ParetoPoint:
    """A point on the cost-quality plane."""
    pipeline: str
    model: str
    avg_cost: float
    avg_quality: float
    run_count: int
    is_pareto_optimal: bool = False
    quality_per_dollar: float = 0.0
    efficiency_rank: int = 0


@dataclass
class CostQualityAnalysis:
    """Complete cost-quality analysis results."""
    pareto_points: List[ParetoPoint] = field(default_factory=list)
    efficiency_rankings: pd.DataFrame = field(default_factory=pd.DataFrame)
    model_comparison: Dict = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


def load_cost_quality_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load runs with quality scores merged."""
    data, stages = load_experiment_data(success_only=True)
    return data, stages


def _check_dominance(args: Tuple[int, 'ParetoPoint', List['ParetoPoint']]) -> Tuple[int, bool]:
    """Check if a point is dominated by any other point (for parallel processing)."""
    idx, p1, all_points = args
    for j, p2 in enumerate(all_points):
        if idx != j:
            # p2 dominates p1 if p2 has lower cost AND higher quality
            if p2.avg_cost <= p1.avg_cost and p2.avg_quality >= p1.avg_quality:
                if p2.avg_cost < p1.avg_cost or p2.avg_quality > p1.avg_quality:
                    return (idx, True)  # is_dominated = True
    return (idx, False)  # is_dominated = False


def calculate_pareto_frontier(
    data: pd.DataFrame,
    parallel: bool = False,
    workers: int = 4,
) -> List[ParetoPoint]:
    """
    Calculate Pareto-optimal pipelines based on cost and quality.

    A point is Pareto-optimal if no other point has both lower cost
    AND higher quality.

    Args:
        data: DataFrame with experiment data
        parallel: Use parallel processing for dominance checks
        workers: Number of parallel workers
    """
    if data.empty or 'combined_score' not in data.columns:
        return []

    # Aggregate by pipeline and model
    agg = data.groupby(['pipeline', 'model']).agg({
        'total_cost': 'mean',
        'combined_score': 'mean',
        'id': 'count',
    }).reset_index()
    agg.columns = ['pipeline', 'model', 'avg_cost', 'avg_quality', 'run_count']

    # Filter out rows with missing quality
    agg = agg.dropna(subset=['avg_quality'])

    if agg.empty:
        return []

    points = []
    for _, row in agg.iterrows():
        quality_per_dollar = (row['avg_quality'] / row['avg_cost'] * 1000) if row['avg_cost'] > 0 else 0

        point = ParetoPoint(
            pipeline=row['pipeline'],
            model=row['model'],
            avg_cost=row['avg_cost'],
            avg_quality=row['avg_quality'],
            run_count=int(row['run_count']),
            quality_per_dollar=quality_per_dollar,
        )
        points.append(point)

    # Determine Pareto optimality
    # A point is Pareto-optimal if no other point dominates it
    # (dominates = lower cost AND higher quality)
    if parallel and len(points) > 10:
        # Parallel dominance checking for larger datasets
        tasks = [(i, p, points) for i, p in enumerate(points)]
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(_check_dominance, tasks))
        for idx, is_dominated in results:
            points[idx].is_pareto_optimal = not is_dominated
    else:
        # Sequential processing for small datasets
        for i, p1 in enumerate(points):
            is_dominated = False
            for j, p2 in enumerate(points):
                if i != j:
                    # p2 dominates p1 if p2 has lower cost AND higher quality
                    if p2.avg_cost <= p1.avg_cost and p2.avg_quality >= p1.avg_quality:
                        if p2.avg_cost < p1.avg_cost or p2.avg_quality > p1.avg_quality:
                            is_dominated = True
                            break
            p1.is_pareto_optimal = not is_dominated

    # Rank by quality per dollar
    points_sorted = sorted(points, key=lambda x: x.quality_per_dollar, reverse=True)
    for rank, point in enumerate(points_sorted, 1):
        point.efficiency_rank = rank

    return points


def score_quality_efficiency(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate quality per dollar for each pipeline/model."""
    if data.empty or 'combined_score' not in data.columns:
        return pd.DataFrame()

    agg = data.groupby(['pipeline', 'model']).agg({
        'total_cost': ['mean', 'std'],
        'combined_score': ['mean', 'std'],
        'id': 'count',
    }).reset_index()

    agg.columns = ['pipeline', 'model', 'avg_cost', 'cost_std',
                   'avg_quality', 'quality_std', 'runs']

    # Quality per dollar (scaled for readability)
    agg['quality_per_dollar'] = (agg['avg_quality'] / agg['avg_cost'] * 1000).round(0)

    # Quality improvement potential (quality / cost ratio relative to min)
    min_ratio = agg['quality_per_dollar'].min()
    agg['efficiency_index'] = (agg['quality_per_dollar'] / min_ratio).round(2)

    return agg.sort_values('quality_per_dollar', ascending=False)


def rank_pipelines_by_efficiency(data: pd.DataFrame) -> pd.DataFrame:
    """Rank pipelines by overall cost-effectiveness."""
    efficiency = score_quality_efficiency(data)

    if efficiency.empty:
        return pd.DataFrame()

    # Add rankings
    efficiency['rank'] = range(1, len(efficiency) + 1)

    # Identify recommendations
    efficiency['recommendation'] = efficiency.apply(
        lambda row: 'Best Value' if row['rank'] == 1
        else 'High Quality' if row['avg_quality'] == efficiency['avg_quality'].max()
        else 'Low Cost' if row['avg_cost'] == efficiency['avg_cost'].min()
        else '',
        axis=1
    )

    return efficiency


def create_pareto_visualization(points: List[ParetoPoint]) -> go.Figure:
    """Generate Pareto frontier scatter plot."""
    if not points:
        return go.Figure()

    # Separate Pareto-optimal and non-optimal points
    pareto_optimal = [p for p in points if p.is_pareto_optimal]
    non_optimal = [p for p in points if not p.is_pareto_optimal]

    fig = go.Figure()

    # Plot non-optimal points
    for model in ['flash', 'pro']:
        model_points = [p for p in non_optimal if model in p.model.lower()]
        if model_points:
            color = FLASH_COLOR if model == 'flash' else PRO_COLOR
            fig.add_trace(go.Scatter(
                x=[p.avg_cost for p in model_points],
                y=[p.avg_quality for p in model_points],
                mode='markers',
                name=f'{model.title()} (non-optimal)',
                marker=dict(color=color, size=10, opacity=0.5),
                text=[f"{p.pipeline}<br>Rank: {p.efficiency_rank}" for p in model_points],
                hovertemplate='%{text}<br>Cost: $%{x:.5f}<br>Quality: %{y:.1f}<extra></extra>',
            ))

    # Plot Pareto-optimal points (larger markers)
    for model in ['flash', 'pro']:
        model_points = [p for p in pareto_optimal if model in p.model.lower()]
        if model_points:
            color = FLASH_COLOR if model == 'flash' else PRO_COLOR
            fig.add_trace(go.Scatter(
                x=[p.avg_cost for p in model_points],
                y=[p.avg_quality for p in model_points],
                mode='markers',
                name=f'{model.title()} (Pareto-optimal)',
                marker=dict(color=color, size=15, symbol='star', line=dict(width=2, color='black')),
                text=[f"{p.pipeline}<br>Rank: {p.efficiency_rank}" for p in model_points],
                hovertemplate='%{text}<br>Cost: $%{x:.5f}<br>Quality: %{y:.1f}<extra></extra>',
            ))

    # Draw Pareto frontier line
    if pareto_optimal:
        frontier_sorted = sorted(pareto_optimal, key=lambda x: x.avg_cost)
        fig.add_trace(go.Scatter(
            x=[p.avg_cost for p in frontier_sorted],
            y=[p.avg_quality for p in frontier_sorted],
            mode='lines',
            name='Pareto Frontier',
            line=dict(color='gray', dash='dash', width=2),
            hoverinfo='skip',
        ))

    fig.update_layout(
        title='Cost vs Quality: Pareto Frontier Analysis',
        xaxis_title='Average Cost ($)',
        yaxis_title='Average Quality Score',
        template=DEFAULT_TEMPLATE,
        width=CHART_CONFIG['width'],
        height=CHART_CONFIG['height'],
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    return fig


def create_efficiency_bar_chart(rankings: pd.DataFrame) -> go.Figure:
    """Create horizontal bar chart of efficiency rankings."""
    if rankings.empty:
        return go.Figure()

    # Create display labels
    rankings = rankings.copy()
    rankings['label'] = rankings['pipeline'] + ' (' + rankings['model'].str.extract(r'(flash|pro)', expand=False).str.title() + ')'

    # Color by model
    colors = [FLASH_COLOR if 'flash' in m.lower() else PRO_COLOR for m in rankings['model']]

    fig = go.Figure(go.Bar(
        x=rankings['quality_per_dollar'],
        y=rankings['label'],
        orientation='h',
        marker_color=colors,
        text=[f'{v:.0f}' for v in rankings['quality_per_dollar']],
        textposition='auto',
    ))

    fig.update_layout(
        title='Quality per Dollar (Higher is Better)',
        xaxis_title='Quality Points per $0.001',
        yaxis_title='Pipeline',
        template=DEFAULT_TEMPLATE,
        width=CHART_CONFIG['width'],
        height=max(400, len(rankings) * 30),
    )

    return fig


def generate_recommendations(points: List[ParetoPoint], rankings: pd.DataFrame) -> List[str]:
    """Generate actionable recommendations based on analysis."""
    recommendations = []

    if not points:
        recommendations.append("No data available for analysis. Run experiments first.")
        return recommendations

    # Find best overall value
    best_value = max(points, key=lambda x: x.quality_per_dollar)
    recommendations.append(
        f"Best Value: {best_value.pipeline} ({best_value.model}) - "
        f"{best_value.quality_per_dollar:.0f} quality points per $0.001"
    )

    # Find Pareto-optimal options
    pareto_optimal = [p for p in points if p.is_pareto_optimal]
    if pareto_optimal:
        recommendations.append(
            f"Pareto-Optimal Choices: {len(pareto_optimal)} pipeline/model combinations "
            "offer the best cost-quality tradeoffs"
        )

    # Compare Flash vs Pro
    flash_points = [p for p in points if 'flash' in p.model.lower()]
    pro_points = [p for p in points if 'pro' in p.model.lower()]

    if flash_points and pro_points:
        flash_avg_efficiency = np.mean([p.quality_per_dollar for p in flash_points])
        pro_avg_efficiency = np.mean([p.quality_per_dollar for p in pro_points])

        if flash_avg_efficiency > pro_avg_efficiency:
            ratio = flash_avg_efficiency / pro_avg_efficiency
            recommendations.append(
                f"Flash is {ratio:.1f}x more cost-efficient than Pro on average"
            )
        else:
            ratio = pro_avg_efficiency / flash_avg_efficiency
            recommendations.append(
                f"Pro is {ratio:.1f}x more cost-efficient than Flash on average"
            )

    # Identify quality-focused option
    highest_quality = max(points, key=lambda x: x.avg_quality)
    if highest_quality.avg_quality > 0:
        recommendations.append(
            f"Highest Quality: {highest_quality.pipeline} ({highest_quality.model}) - "
            f"Score: {highest_quality.avg_quality:.1f}"
        )

    # Identify lowest cost option
    lowest_cost = min(points, key=lambda x: x.avg_cost)
    recommendations.append(
        f"Lowest Cost: {lowest_cost.pipeline} ({lowest_cost.model}) - "
        f"${lowest_cost.avg_cost:.5f}/run"
    )

    return recommendations


def run_cost_quality_analysis(
    model: Optional[str] = None,
    parallel: bool = False,
    workers: int = 4,
    show_charts: bool = True,
    save_charts: bool = False,
    output_dir: str = "figures",
) -> CostQualityAnalysis:
    """
    Run complete cost-quality frontier analysis.

    Args:
        model: Filter by model (optional)
        parallel: Use parallel processing for data loading
        workers: Number of parallel workers
        show_charts: Display charts interactively
        save_charts: Save charts to output directory
        output_dir: Directory for saved charts

    Returns:
        CostQualityAnalysis with all results
    """
    print("\n" + "=" * 70)
    print("COST-QUALITY FRONTIER ANALYSIS")
    print("=" * 70)

    # Load data
    print("\nLoading experiment data...")
    data, stages = load_cost_quality_data()

    if data.empty:
        print("No experiment data found. Run experiments first.")
        return CostQualityAnalysis(recommendations=["No data available"])

    # Filter by model if specified
    if model:
        data = data[data['model'].str.contains(model, case=False, na=False)]

    print(f"Analyzing {len(data)} runs...")

    # Calculate Pareto frontier
    if parallel:
        print(f"\nCalculating Pareto frontier (parallel, {workers} workers)...")
    else:
        print("\nCalculating Pareto frontier...")
    points = calculate_pareto_frontier(data, parallel=parallel, workers=workers)

    # Score efficiency
    print("Scoring quality efficiency...")
    rankings = rank_pipelines_by_efficiency(data)

    # Generate recommendations
    print("Generating recommendations...")
    recommendations = generate_recommendations(points, rankings)

    # Create analysis result
    analysis = CostQualityAnalysis(
        pareto_points=points,
        efficiency_rankings=rankings,
        recommendations=recommendations,
    )

    # Print results
    print("\n" + "-" * 70)
    print("PARETO-OPTIMAL PIPELINES")
    print("-" * 70)

    pareto_optimal = [p for p in points if p.is_pareto_optimal]
    for p in pareto_optimal:
        print(f"  ★ {p.pipeline} ({p.model})")
        print(f"    Cost: ${p.avg_cost:.5f}  Quality: {p.avg_quality:.1f}  Efficiency Rank: #{p.efficiency_rank}")

    print("\n" + "-" * 70)
    print("EFFICIENCY RANKINGS (Top 10)")
    print("-" * 70)

    if not rankings.empty:
        top_10 = rankings.head(10)
        for _, row in top_10.iterrows():
            marker = "★" if row.get('recommendation') else " "
            print(f"  {marker} #{int(row['rank'])}: {row['pipeline']} ({row['model']})")
            print(f"      Quality/$ : {row['quality_per_dollar']:.0f}  |  Quality: {row['avg_quality']:.1f}  |  Cost: ${row['avg_cost']:.5f}")

    print("\n" + "-" * 70)
    print("RECOMMENDATIONS")
    print("-" * 70)
    for rec in recommendations:
        print(f"  • {rec}")

    # Generate charts
    if show_charts or save_charts:
        from pathlib import Path

        # Pareto frontier chart
        pareto_fig = create_pareto_visualization(points)
        if show_charts and pareto_fig.data:
            pareto_fig.show()
        if save_charts and pareto_fig.data:
            Path(output_dir).mkdir(exist_ok=True)
            pareto_fig.write_html(f"{output_dir}/pareto_frontier.html")
            print(f"\n  Saved: {output_dir}/pareto_frontier.html")

        # Efficiency bar chart
        efficiency_fig = create_efficiency_bar_chart(rankings)
        if show_charts and efficiency_fig.data:
            efficiency_fig.show()
        if save_charts and efficiency_fig.data:
            efficiency_fig.write_html(f"{output_dir}/efficiency_rankings.html")
            print(f"  Saved: {output_dir}/efficiency_rankings.html")

    print("\n" + "=" * 70)

    return analysis


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cost-Quality Frontier Analysis"
    )

    parser.add_argument(
        "--model",
        choices=["flash", "pro"],
        help="Filter analysis by model"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Use parallel processing"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers"
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip chart display"
    )
    parser.add_argument(
        "--save-charts",
        action="store_true",
        help="Save charts to output directory"
    )
    parser.add_argument(
        "--output-dir",
        default="figures",
        help="Output directory for charts"
    )

    args = parser.parse_args()

    run_cost_quality_analysis(
        model=args.model,
        parallel=args.parallel,
        workers=args.workers,
        show_charts=not args.no_charts,
        save_charts=args.save_charts,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
