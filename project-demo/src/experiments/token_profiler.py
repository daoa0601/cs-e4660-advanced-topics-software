"""
Token Distribution Profiler

Analyzes token distribution patterns across workflows to identify:
- Input/output token ratios per stage
- Token distribution histograms
- Context growth patterns in multi-turn workflows
- Cost impact of token distribution

Usage:
    python3 -m src.experiments.token_profiler --workflow verbosity --model flash
    python3 -m src.experiments.token_profiler --all-workflows
"""

import argparse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.db import get_runs, get_stages, get_quality_scores
from src.visualization import (
    FLASH_COLOR,
    PRO_COLOR,
    MODEL_COLORS,
    DEFAULT_TEMPLATE,
    CHART_CONFIG,
)


@dataclass
class TokenDistribution:
    """Token distribution data for a single stage/workflow."""
    workflow: str
    stage_type: str
    model: str
    input_tokens: List[int] = field(default_factory=list)
    output_tokens: List[int] = field(default_factory=list)

    @property
    def input_mean(self) -> float:
        return np.mean(self.input_tokens) if self.input_tokens else 0

    @property
    def output_mean(self) -> float:
        return np.mean(self.output_tokens) if self.output_tokens else 0

    @property
    def input_output_ratio(self) -> float:
        if self.output_mean == 0:
            return 0
        return self.input_mean / self.output_mean

    @property
    def total_tokens(self) -> int:
        return sum(self.input_tokens) + sum(self.output_tokens)


@dataclass
class TokenProfile:
    """Complete token profile for a workflow/model combination."""
    workflow: str
    model: str
    distributions: List[TokenDistribution] = field(default_factory=list)
    context_growth: List[int] = field(default_factory=list)
    total_runs: int = 0

    @property
    def total_input_tokens(self) -> int:
        return sum(d.input_mean * len(d.input_tokens) for d in self.distributions)

    @property
    def total_output_tokens(self) -> int:
        return sum(d.output_mean * len(d.output_tokens) for d in self.distributions)

    @property
    def overall_input_output_ratio(self) -> float:
        if self.total_output_tokens == 0:
            return 0
        return self.total_input_tokens / self.total_output_tokens

    def get_stage_ratios(self) -> Dict[str, float]:
        """Get input/output ratio by stage type."""
        return {d.stage_type: d.input_output_ratio for d in self.distributions}


def load_token_data(
    workflow: Optional[str] = None,
    model: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load token data from database."""
    runs_df = get_runs(workflow=workflow, model=model, success_only=True)
    stages_df = get_stages()

    if not runs_df.empty and not stages_df.empty:
        # Filter stages to only those from our runs
        run_ids = runs_df['id'].tolist()
        stages_df = stages_df[stages_df['run_id'].isin(run_ids)]

    return runs_df, stages_df


def build_token_profile(
    workflow: str,
    model: str,
    runs_df: pd.DataFrame,
    stages_df: pd.DataFrame,
) -> TokenProfile:
    """Build a token profile from run and stage data."""
    profile = TokenProfile(workflow=workflow, model=model)

    # Filter to this workflow/model
    filtered_runs = runs_df[
        (runs_df['workflow'] == workflow) &
        (runs_df['model'].str.contains(model, case=False, na=False))
    ]

    if filtered_runs.empty:
        return profile

    profile.total_runs = len(filtered_runs)

    # Get stages for these runs
    run_ids = filtered_runs['id'].tolist()
    filtered_stages = stages_df[stages_df['run_id'].isin(run_ids)]

    # Build distributions by stage type
    stage_types = filtered_stages['stage_type'].unique()
    for stage_type in stage_types:
        stage_data = filtered_stages[filtered_stages['stage_type'] == stage_type]

        dist = TokenDistribution(
            workflow=workflow,
            stage_type=stage_type,
            model=model,
            input_tokens=stage_data['input_tokens'].dropna().astype(int).tolist(),
            output_tokens=stage_data['output_tokens'].dropna().astype(int).tolist(),
        )
        profile.distributions.append(dist)

    # Extract context growth for multi-turn workflows
    if 'context_tokens_by_turn' in filtered_runs.columns:
        for _, row in filtered_runs.iterrows():
            if pd.notna(row.get('context_tokens_by_turn')):
                try:
                    context_data = json.loads(row['context_tokens_by_turn'])
                    if isinstance(context_data, list):
                        profile.context_growth.extend(context_data)
                except (json.JSONDecodeError, TypeError):
                    pass

    return profile


def profile_all_workflows(model: Optional[str] = None) -> Dict[str, TokenProfile]:
    """Profile all available workflows."""
    runs_df, stages_df = load_token_data(model=model)

    if runs_df.empty:
        return {}

    profiles = {}
    workflows = runs_df['workflow'].unique()

    for workflow in workflows:
        models_in_workflow = runs_df[runs_df['workflow'] == workflow]['model'].unique()

        for model_name in models_in_workflow:
            # Normalize model name
            model_key = 'flash' if 'flash' in model_name.lower() else 'pro'
            profile_key = f"{workflow}_{model_key}"

            profile = build_token_profile(workflow, model_name, runs_df, stages_df)
            if profile.total_runs > 0:
                profiles[profile_key] = profile

    return profiles


def generate_token_histogram(profile: TokenProfile) -> go.Figure:
    """Generate token distribution histogram for a profile."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Input Tokens', 'Output Tokens'),
    )

    # Collect all tokens by stage
    all_input = []
    all_output = []
    stage_labels_input = []
    stage_labels_output = []

    for dist in profile.distributions:
        all_input.extend(dist.input_tokens)
        all_output.extend(dist.output_tokens)
        stage_labels_input.extend([dist.stage_type] * len(dist.input_tokens))
        stage_labels_output.extend([dist.stage_type] * len(dist.output_tokens))

    color = MODEL_COLORS.get(profile.model, FLASH_COLOR)

    # Input histogram
    if all_input:
        fig.add_trace(
            go.Histogram(x=all_input, name='Input', marker_color=color, opacity=0.7),
            row=1, col=1
        )

    # Output histogram
    if all_output:
        fig.add_trace(
            go.Histogram(x=all_output, name='Output', marker_color=color, opacity=0.7),
            row=1, col=2
        )

    fig.update_layout(
        title=f'Token Distribution: {profile.workflow} ({profile.model})',
        template=DEFAULT_TEMPLATE,
        width=CHART_CONFIG['width'],
        height=CHART_CONFIG['height'] // 2,
        showlegend=False,
    )

    fig.update_xaxes(title_text='Token Count', row=1, col=1)
    fig.update_xaxes(title_text='Token Count', row=1, col=2)
    fig.update_yaxes(title_text='Frequency', row=1, col=1)
    fig.update_yaxes(title_text='Frequency', row=1, col=2)

    return fig


def generate_ratio_comparison(profiles: Dict[str, TokenProfile]) -> go.Figure:
    """Generate input/output ratio comparison across workflows."""
    data = []

    for key, profile in profiles.items():
        for dist in profile.distributions:
            if dist.input_output_ratio > 0:
                data.append({
                    'workflow': profile.workflow,
                    'model': 'Flash' if 'flash' in profile.model.lower() else 'Pro',
                    'stage_type': dist.stage_type,
                    'ratio': dist.input_output_ratio,
                    'input_mean': dist.input_mean,
                    'output_mean': dist.output_mean,
                })

    if not data:
        return go.Figure()

    df = pd.DataFrame(data)

    fig = px.bar(
        df,
        x='stage_type',
        y='ratio',
        color='model',
        facet_col='workflow',
        color_discrete_map={'Flash': FLASH_COLOR, 'Pro': PRO_COLOR},
        title='Input/Output Token Ratio by Stage and Workflow',
        labels={'ratio': 'Input/Output Ratio', 'stage_type': 'Stage Type'},
    )

    fig.update_layout(
        template=DEFAULT_TEMPLATE,
        width=CHART_CONFIG['width'],
        height=CHART_CONFIG['height'],
    )

    return fig


def generate_context_growth_chart(profiles: Dict[str, TokenProfile]) -> go.Figure:
    """Generate context growth chart for multi-turn workflows."""
    fig = go.Figure()

    for key, profile in profiles.items():
        if profile.context_growth:
            # Calculate average growth per turn
            turns = len(profile.context_growth)
            if turns > 1:
                color = FLASH_COLOR if 'flash' in profile.model.lower() else PRO_COLOR
                fig.add_trace(go.Scatter(
                    x=list(range(1, turns + 1)),
                    y=profile.context_growth,
                    name=f'{profile.workflow} ({profile.model})',
                    mode='lines+markers',
                    marker=dict(color=color),
                    line=dict(color=color),
                ))

    if not fig.data:
        return fig

    fig.update_layout(
        title='Context Token Growth Across Turns',
        xaxis_title='Turn',
        yaxis_title='Context Tokens',
        template=DEFAULT_TEMPLATE,
        width=CHART_CONFIG['width'],
        height=CHART_CONFIG['height'],
    )

    return fig


def generate_summary_table(profiles: Dict[str, TokenProfile]) -> pd.DataFrame:
    """Generate summary statistics table."""
    rows = []

    for key, profile in profiles.items():
        model_name = 'Flash' if 'flash' in profile.model.lower() else 'Pro'

        rows.append({
            'Workflow': profile.workflow,
            'Model': model_name,
            'Runs': profile.total_runs,
            'Avg Input Tokens': int(profile.total_input_tokens / max(1, profile.total_runs)),
            'Avg Output Tokens': int(profile.total_output_tokens / max(1, profile.total_runs)),
            'I/O Ratio': round(profile.overall_input_output_ratio, 2),
            'Stages': len(profile.distributions),
        })

    return pd.DataFrame(rows).sort_values(['Workflow', 'Model'])


def analyze_token_patterns(profiles: Dict[str, TokenProfile]) -> Dict:
    """Analyze token patterns and return insights."""
    insights = {
        'high_input_stages': [],
        'high_output_stages': [],
        'model_differences': [],
        'recommendations': [],
    }

    # Find stages with high input tokens (potential for caching)
    for key, profile in profiles.items():
        for dist in profile.distributions:
            if dist.input_mean > 1000:
                insights['high_input_stages'].append({
                    'workflow': profile.workflow,
                    'stage': dist.stage_type,
                    'model': profile.model,
                    'avg_input': int(dist.input_mean),
                })

            if dist.output_mean > 500:
                insights['high_output_stages'].append({
                    'workflow': profile.workflow,
                    'stage': dist.stage_type,
                    'model': profile.model,
                    'avg_output': int(dist.output_mean),
                })

    # Compare Flash vs Pro
    workflows = set(p.workflow for p in profiles.values())
    for workflow in workflows:
        flash_profile = profiles.get(f"{workflow}_flash")
        pro_profile = profiles.get(f"{workflow}_pro")

        if flash_profile and pro_profile:
            flash_total = flash_profile.total_input_tokens + flash_profile.total_output_tokens
            pro_total = pro_profile.total_input_tokens + pro_profile.total_output_tokens

            if flash_total > 0 and pro_total > 0:
                ratio = pro_total / flash_total
                insights['model_differences'].append({
                    'workflow': workflow,
                    'flash_tokens': int(flash_total),
                    'pro_tokens': int(pro_total),
                    'ratio': round(ratio, 2),
                })

    # Generate recommendations
    if insights['high_input_stages']:
        insights['recommendations'].append(
            "Consider context caching for stages with high input tokens"
        )

    if insights['high_output_stages']:
        insights['recommendations'].append(
            "Review output verbosity for stages with high output tokens"
        )

    return insights


def print_token_profile_report(profiles: Dict[str, TokenProfile]):
    """Print a comprehensive token profile report."""
    print("\n" + "=" * 70)
    print("TOKEN DISTRIBUTION PROFILE REPORT")
    print("=" * 70)

    # Summary table
    summary_df = generate_summary_table(profiles)
    if not summary_df.empty:
        print("\n📊 Summary Statistics")
        print("-" * 70)
        print(summary_df.to_string(index=False))

    # Detailed stage breakdown
    print("\n\n📈 Stage-Level Token Analysis")
    print("-" * 70)

    for key, profile in sorted(profiles.items()):
        print(f"\n{profile.workflow.upper()} ({profile.model})")
        print(f"  Total runs: {profile.total_runs}")

        for dist in profile.distributions:
            print(f"  {dist.stage_type}:")
            print(f"    Input:  {dist.input_mean:,.0f} avg ({len(dist.input_tokens)} samples)")
            print(f"    Output: {dist.output_mean:,.0f} avg ({len(dist.output_tokens)} samples)")
            print(f"    Ratio:  {dist.input_output_ratio:.2f}")

    # Insights
    insights = analyze_token_patterns(profiles)

    print("\n\n💡 Insights")
    print("-" * 70)

    if insights['high_input_stages']:
        print("\nHigh Input Token Stages (>1000 avg):")
        for item in insights['high_input_stages'][:5]:
            print(f"  • {item['workflow']}/{item['stage']}: {item['avg_input']:,} tokens")

    if insights['model_differences']:
        print("\nModel Token Comparison:")
        for item in insights['model_differences']:
            print(f"  • {item['workflow']}: Pro uses {item['ratio']:.1f}x tokens vs Flash")

    if insights['recommendations']:
        print("\nRecommendations:")
        for rec in insights['recommendations']:
            print(f"  ✓ {rec}")

    print("\n" + "=" * 70)


def run_token_profiler(
    workflow: Optional[str] = None,
    model: Optional[str] = None,
    show_charts: bool = True,
    save_charts: bool = False,
    output_dir: str = "figures",
):
    """Run the token distribution profiler."""
    print(f"\n📊 Running Token Distribution Profiler...")

    if workflow:
        runs_df, stages_df = load_token_data(workflow=workflow, model=model)
        if runs_df.empty:
            print(f"No data found for workflow '{workflow}'")
            return None

        profiles = {}
        models = runs_df['model'].unique()
        for m in models:
            model_key = 'flash' if 'flash' in m.lower() else 'pro'
            profile = build_token_profile(workflow, m, runs_df, stages_df)
            if profile.total_runs > 0:
                profiles[f"{workflow}_{model_key}"] = profile
    else:
        profiles = profile_all_workflows(model=model)

    if not profiles:
        print("No token data available. Run experiments first.")
        return None

    # Print report
    print_token_profile_report(profiles)

    # Generate charts
    if show_charts or save_charts:
        from pathlib import Path

        # Histogram for each profile
        for key, profile in profiles.items():
            fig = generate_token_histogram(profile)
            if show_charts:
                fig.show()
            if save_charts:
                Path(output_dir).mkdir(exist_ok=True)
                fig.write_html(f"{output_dir}/token_histogram_{key}.html")

        # Ratio comparison
        ratio_fig = generate_ratio_comparison(profiles)
        if ratio_fig.data:
            if show_charts:
                ratio_fig.show()
            if save_charts:
                ratio_fig.write_html(f"{output_dir}/token_ratios.html")

        # Context growth
        growth_fig = generate_context_growth_chart(profiles)
        if growth_fig.data:
            if show_charts:
                growth_fig.show()
            if save_charts:
                growth_fig.write_html(f"{output_dir}/context_growth.html")

    return profiles


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Token Distribution Profiler for LLM Cost Analysis"
    )

    parser.add_argument(
        "--workflow",
        choices=["verbosity", "context", "react", "multiturn", "self_correcting", "document"],
        help="Specific workflow to profile (default: all)"
    )
    parser.add_argument(
        "--model",
        choices=["flash", "pro"],
        help="Specific model to profile (default: both)"
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip chart generation"
    )
    parser.add_argument(
        "--save-charts",
        action="store_true",
        help="Save charts to figures/ directory"
    )
    parser.add_argument(
        "--output-dir",
        default="figures",
        help="Output directory for charts (default: figures)"
    )

    args = parser.parse_args()

    run_token_profiler(
        workflow=args.workflow,
        model=args.model,
        show_charts=not args.no_charts,
        save_charts=args.save_charts,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
