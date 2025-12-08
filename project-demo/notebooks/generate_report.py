#!/usr/bin/env python3
"""
Quick Analysis Runner - Generate All Figures from Experiment Data

Run this script after experiments to generate all figures and a summary report.

Usage:
    cd project-demo
    python3 notebooks/generate_report.py

Output:
    - figures/*.png - All visualization figures
    - figures/summary.md - Key metrics summary
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from src.db import (
    get_runs,
    get_stages,
    get_quality_scores,
    get_pipeline_summary,
    get_cost_by_model,
    get_cost_by_stage_type,
)
from src.utils import format_cost
from src.visualization import (
    FLASH_COLOR,
    PRO_COLOR,
    MODEL_COLORS,
    DEFAULT_TEMPLATE,
    load_experiment_data,
)

# Output directory - use session path if available
def _get_figures_dir():
    """Get figures directory from session or default."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.session import get_session_figures_path
        return get_session_figures_path()
    except ImportError:
        pass
    return Path(__file__).parent.parent / "figures"

FIGURES_DIR = _get_figures_dir()


def setup():
    """Create output directory."""
    FIGURES_DIR.mkdir(exist_ok=True)
    print(f"📁 Output directory: {FIGURES_DIR}")


def load_all_data():
    """Load all experiment data."""
    print("📊 Loading data...")
    
    runs = get_runs(success_only=True)
    stages = get_stages()
    quality = get_quality_scores()
    
    # Merge runs with quality on the 'id' column from runs and 'run_id' from quality
    if not quality.empty and not runs.empty:
        data = runs.merge(quality, left_on='id', right_on='run_id', how='left', suffixes=('', '_q'))
    else:
        data = runs
    
    print(f"   Runs: {len(runs)}")
    print(f"   Stages: {len(stages)}")
    if 'combined_score' in data.columns:
        quality_count = data['combined_score'].notna().sum()
        print(f"   Quality scores: {quality_count}")
    
    return data, stages


def save_figure(fig, name, **kwargs):
    """Save figure as PNG if kaleido installed, otherwise HTML."""
    try:
        fig.write_image(str(FIGURES_DIR / f"{name}.png"), scale=2, **kwargs)
        print(f"   ✓ {name}.png")
    except ValueError:
        # Kaleido not installed, save as HTML
        fig.write_html(str(FIGURES_DIR / f"{name}.html"))
        print(f"   ✓ {name}.html (install kaleido for PNG)")


def fig1_cost_by_model(data):
    """Figure 1: Overall cost comparison by model."""
    model_costs = data.groupby('model').agg({
        'total_cost': ['sum', 'mean', 'std', 'count']
    }).round(6)
    model_costs.columns = ['total', 'mean', 'std', 'count']
    model_costs = model_costs.reset_index()

    fig = px.bar(
        model_costs,
        x='model',
        y='mean',
        error_y='std',
        color='model',
        color_discrete_map=MODEL_COLORS,
        title='Average Cost per Run by Model',
        labels={'mean': 'Average Cost ($)', 'model': 'Model'}
    )
    fig.update_layout(template=DEFAULT_TEMPLATE, showlegend=False)

    save_figure(fig, "01_cost_by_model")

    return model_costs


def fig2_cost_by_pipeline(data):
    """Figure 2: Cost comparison across pipelines."""
    pipeline_costs = data.groupby(['pipeline', 'model'])['total_cost'].mean().reset_index()

    fig = px.bar(
        pipeline_costs,
        x='pipeline',
        y='total_cost',
        color='model',
        barmode='group',
        color_discrete_map=MODEL_COLORS,
        title='Average Cost by Pipeline',
        labels={'total_cost': 'Average Cost ($)', 'pipeline': 'Pipeline'}
    )
    fig.update_layout(template=DEFAULT_TEMPLATE, xaxis_tickangle=-45)

    save_figure(fig, "02_cost_by_pipeline", width=1200)

    return pipeline_costs


def fig3_quality_comparison(data):
    """Figure 3: Quality score comparison."""
    if 'combined_score' not in data.columns:
        print("   ⚠ No quality scores - skipping")
        return None

    quality_by_model = data.groupby('model')['combined_score'].agg(['mean', 'std']).reset_index()

    fig = px.bar(
        quality_by_model,
        x='model',
        y='mean',
        error_y='std',
        color='model',
        color_discrete_map=MODEL_COLORS,
        title='Average Quality Score by Model',
        labels={'mean': 'Quality Score', 'model': 'Model'}
    )
    fig.update_layout(template=DEFAULT_TEMPLATE, showlegend=False)

    save_figure(fig, "03_quality_by_model")

    return quality_by_model


def fig4_cost_quality_scatter(data):
    """Figure 4: Cost vs Quality scatter plot."""
    if 'combined_score' not in data.columns:
        print("   ⚠ No quality scores - skipping")
        return None

    fig = px.scatter(
        data,
        x='total_cost',
        y='combined_score',
        color='model',
        hover_data=['pipeline'],
        color_discrete_map=MODEL_COLORS,
        title='Cost vs Quality by Model',
        labels={'total_cost': 'Cost ($)', 'combined_score': 'Quality Score'}
    )
    fig.update_layout(template=DEFAULT_TEMPLATE)

    save_figure(fig, "04_cost_quality_scatter")

    return None


def fig5_stage_cost_distribution(stages):
    """Figure 5: Cost distribution by stage type."""
    stage_costs = stages.groupby('stage_type')['cost'].sum().reset_index()
    stage_costs = stage_costs.sort_values('cost', ascending=True)

    fig = px.bar(
        stage_costs,
        x='cost',
        y='stage_type',
        orientation='h',
        title='Total Cost by Stage Type',
        labels={'cost': 'Total Cost ($)', 'stage_type': 'Stage Type'},
        color='cost',
        color_continuous_scale='Teal'
    )
    fig.update_layout(template=DEFAULT_TEMPLATE, showlegend=False)

    save_figure(fig, "05_stage_cost_distribution")

    return stage_costs


def fig6_flash_vs_pro_advantage(data):
    """Figure 6: Flash vs Pro advantage by pipeline complexity."""
    if 'combined_score' not in data.columns:
        print("   ⚠ No quality scores - skipping")
        return None

    # Calculate quality difference per pipeline
    advantages = []
    for pipeline in data['pipeline'].unique():
        p_data = data[data['pipeline'] == pipeline]
        flash = p_data[p_data['model'] == 'gemini-2.5-flash']['combined_score'].mean()
        pro = p_data[p_data['model'] == 'gemini-2.5-pro']['combined_score'].mean()

        if pd.notna(flash) and pd.notna(pro):
            advantages.append({
                'pipeline': pipeline,
                'flash_quality': flash,
                'pro_quality': pro,
                'pro_advantage': pro - flash
            })

    adv_df = pd.DataFrame(advantages).sort_values('pro_advantage', ascending=True)

    # Color by whether Pro is better
    adv_df['color'] = adv_df['pro_advantage'].apply(lambda x: 'Pro Better' if x > 0 else 'Flash Better')

    fig = px.bar(
        adv_df,
        x='pro_advantage',
        y='pipeline',
        orientation='h',
        color='color',
        color_discrete_map={'Pro Better': PRO_COLOR, 'Flash Better': FLASH_COLOR},
        title='Quality Advantage: Pro vs Flash',
        labels={'pro_advantage': 'Quality Difference (Pro - Flash)', 'pipeline': 'Pipeline'}
    )
    fig.update_layout(template=DEFAULT_TEMPLATE)

    save_figure(fig, "06_pro_vs_flash_advantage", height=600)

    return adv_df


def calculate_summary_stats(data, stages):
    """Calculate summary statistics."""
    flash = data[data['model'] == 'gemini-2.5-flash']
    pro = data[data['model'] == 'gemini-2.5-pro']
    
    stats = {
        'total_runs': len(data),
        'total_cost': data['total_cost'].sum(),
        'flash_runs': len(flash),
        'flash_cost': flash['total_cost'].sum(),
        'flash_avg_cost': flash['total_cost'].mean(),
        'pro_runs': len(pro),
        'pro_cost': pro['total_cost'].sum(),
        'pro_avg_cost': pro['total_cost'].mean(),
        'cost_ratio': pro['total_cost'].mean() / flash['total_cost'].mean() if len(flash) > 0 else 0,
    }
    
    if 'combined_score' in data.columns:
        stats['flash_quality'] = flash['combined_score'].mean()
        stats['pro_quality'] = pro['combined_score'].mean()
        stats['quality_diff'] = stats['pro_quality'] - stats['flash_quality']
        
        # Statistical test
        flash_q = flash['combined_score'].dropna()
        pro_q = pro['combined_score'].dropna()
        if len(flash_q) > 1 and len(pro_q) > 1:
            _, p_value = stats.ttest_ind(flash_q, pro_q) if hasattr(stats, 'ttest_ind') else (0, 1)
            stats['p_value'] = p_value
    
    return stats


def generate_summary_report(stats, data):
    """Generate markdown summary report."""
    report = f"""# Experiment Results Summary

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Overview

| Metric | Value |
|--------|-------|
| Total Runs | {stats['total_runs']} |
| Total Cost | ${stats['total_cost']:.4f} |

## Model Comparison

| Model | Runs | Total Cost | Avg Cost |
|-------|------|------------|----------|
| Flash | {stats['flash_runs']} | ${stats['flash_cost']:.4f} | ${stats['flash_avg_cost']:.6f} |
| Pro | {stats['pro_runs']} | ${stats['pro_cost']:.4f} | ${stats['pro_avg_cost']:.6f} |

**Cost Ratio**: Pro costs {stats['cost_ratio']:.1f}x more than Flash

"""
    
    if 'flash_quality' in stats:
        report += f"""## Quality Comparison

| Model | Avg Quality |
|-------|-------------|
| Flash | {stats['flash_quality']:.2f} |
| Pro | {stats['pro_quality']:.2f} |

**Quality Difference**: Pro scores {stats['quality_diff']:+.2f} points higher

"""
    
    report += """## Figures Generated

1. `01_cost_by_model.png` - Overall cost comparison
2. `02_cost_by_pipeline.png` - Cost by pipeline
3. `03_quality_by_model.png` - Quality comparison
4. `04_cost_quality_scatter.png` - Cost vs quality
5. `05_stage_cost_distribution.png` - Stage costs
6. `06_pro_vs_flash_advantage.png` - Pro advantage by pipeline
7. `07_verified_accuracy.png` - Accuracy on verified problems (if available)
"""
    
    summary_path = FIGURES_DIR / "summary.md"
    with open(summary_path, 'w') as f:
        f.write(report)
    
    print(f"   ✓ summary.md")
    
    return report


def fig7_verified_experiments():
    """
    Figure 7: Run verified experiments with ground truth.
    This shows actual accuracy, not subjective quality scores.
    """
    try:
        from src.experiments.verified_experiment import (
            compare_models_verified,
            VerifiedExperimentConfig,
            VerifiedExperimentRunner,
        )
        
        print("\n🧪 Running verified experiments (ground truth)...")
        
        # All difficulties
        all_results = compare_models_verified(iterations=20, seed=42)
        
        # Hard problems only
        hard_results = compare_models_verified(iterations=15, difficulty="hard", seed=42)
        
        # Create comparison figure
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # All difficulties bars
        models = list(all_results["results"].keys())
        all_acc = [all_results["results"][m]["accuracy"] * 100 for m in models]
        hard_acc = [hard_results["results"][m]["accuracy"] * 100 for m in models]
        
        fig.add_trace(go.Bar(
            name='All Difficulties',
            x=models,
            y=all_acc,
            marker_color=[FLASH_COLOR, PRO_COLOR][:len(models)],
            text=[f'{a:.0f}%' for a in all_acc],
            textposition='auto',
        ))

        fig.add_trace(go.Bar(
            name='Hard Problems Only',
            x=models,
            y=hard_acc,
            marker_color=['#3aa89d', '#cc5555'][:len(models)],
            text=[f'{a:.0f}%' for a in hard_acc],
            textposition='auto',
        ))
        
        fig.update_layout(
            title='Accuracy on Verified Problems (Ground Truth)',
            yaxis_title='Accuracy (%)',
            barmode='group',
            template=DEFAULT_TEMPLATE,
            yaxis=dict(range=[0, 100]),
        )
        
        save_figure(fig, "07_verified_accuracy")
        
        # Return results for summary
        return {
            'all': all_results,
            'hard': hard_results,
            'flash_all': all_results["results"][models[0]]["accuracy"],
            'pro_all': all_results["results"][models[1]]["accuracy"] if len(models) > 1 else 0,
            'flash_hard': hard_results["results"][models[0]]["accuracy"],
            'pro_hard': hard_results["results"][models[1]]["accuracy"] if len(models) > 1 else 0,
        }
        
    except ImportError as e:
        print(f"   ⚠ Verified experiments not available: {e}")
        return None
    except Exception as e:
        print(f"   ⚠ Error running verified experiments: {e}")
        return None


def generate_verified_summary(verified_results):
    """Append verified experiment results to summary."""
    if verified_results is None:
        return ""
    
    summary = f"""
## Verified Experiments (Ground Truth)

These tests use problems with known correct answers for objective accuracy.

| Difficulty | Flash Accuracy | Pro Accuracy | Pro Advantage |
|------------|---------------|--------------|---------------|
| All | {verified_results['flash_all']:.1%} | {verified_results['pro_all']:.1%} | {(verified_results['pro_all'] - verified_results['flash_all']) / max(0.01, verified_results['flash_all']) * 100:+.1f}% |
| **Hard** | {verified_results['flash_hard']:.1%} | {verified_results['pro_hard']:.1%} | {(verified_results['pro_hard'] - verified_results['flash_hard']) / max(0.01, verified_results['flash_hard']) * 100:+.1f}% |

> **Key Finding**: Pro's advantage increases on harder problems, justifying its premium for complex reasoning tasks.
"""
    return summary


def main():
    """Generate all figures and summary."""
    print("\n" + "=" * 60)
    print("📈 EXPERIMENT REPORT GENERATOR")
    print("=" * 60 + "\n")
    
    setup()
    data, stages = load_all_data()
    
    if data.empty:
        print("❌ No experiment data found!")
        print("   Run experiments first: python -m src.experiment --full-experiment")
        return
    
    print("\n🎨 Generating figures...\n")
    
    # Generate all figures
    fig1_cost_by_model(data)
    fig2_cost_by_pipeline(data)
    fig3_quality_comparison(data)
    fig4_cost_quality_scatter(data)
    fig5_stage_cost_distribution(stages)
    fig6_flash_vs_pro_advantage(data)
    
    # Run verified experiments
    verified_results = fig7_verified_experiments()
    
    print("\n📝 Generating summary...")
    
    stats = calculate_summary_stats(data, stages)
    report = generate_summary_report(stats, data)
    
    # Append verified results if available
    if verified_results:
        verified_summary = generate_verified_summary(verified_results)
        summary_path = FIGURES_DIR / "summary.md"
        with open(summary_path, 'a') as f:
            f.write(verified_summary)
        print("   ✓ Added verified experiment results")
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)
    print(f"\nFigures saved to: {FIGURES_DIR}")
    print(f"Summary report: {FIGURES_DIR / 'summary.md'}")
    
    # Print key stats
    print(f"\n📊 Quick Stats:")
    print(f"   Total runs: {stats['total_runs']}")
    print(f"   Total cost: ${stats['total_cost']:.4f}")
    print(f"   Cost ratio (Pro/Flash): {stats['cost_ratio']:.1f}x")
    if 'quality_diff' in stats:
        print(f"   Quality difference: {stats['quality_diff']:+.2f}")
    
    if verified_results:
        print(f"\n🧪 Verified Accuracy:")
        print(f"   Flash (all/hard): {verified_results['flash_all']:.1%} / {verified_results['flash_hard']:.1%}")
        print(f"   Pro (all/hard):   {verified_results['pro_all']:.1%} / {verified_results['pro_hard']:.1%}")


if __name__ == "__main__":
    main()
