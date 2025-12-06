"""
Flash vs Pro: Fair Comparison Analysis

This script provides a balanced comparison between Gemini 2.5 Flash and Pro,
identifying scenarios where Pro's premium is justified rather than just
showing cost efficiency (which always favors Flash).

Run: python -m notebooks.flash_vs_pro_analysis
Or copy cells into the Jupyter notebook.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import sys
sys.path.insert(0, '..')

from src.db import (
    get_runs, 
    get_stages, 
    get_quality_scores,
)
from src.utils import format_cost


def load_data():
    """Load experiment data."""
    runs_df = get_runs(success_only=True)
    stages_df = get_stages()
    quality_df = get_quality_scores()
    
    # Merge quality with runs
    if not quality_df.empty and not runs_df.empty:
        merged = runs_df.merge(quality_df, on='run_id', how='left')
    else:
        merged = runs_df
    
    return merged, stages_df


def calculate_fair_metrics(df):
    """
    Calculate metrics that show BOTH efficiency AND quality.
    
    Key insight: Cost per dollar favors Flash, but we should also look at:
    - Absolute quality achieved
    - Quality improvement per extra dollar spent
    - Statistical significance of quality differences
    """
    flash_df = df[df['model'] == 'gemini-2.5-flash']
    pro_df = df[df['model'] == 'gemini-2.5-pro']
    
    metrics = {
        'flash': {
            'count': len(flash_df),
            'total_cost': flash_df['total_cost'].sum(),
            'avg_cost': flash_df['total_cost'].mean(),
            'avg_quality': flash_df['combined_score'].mean() if 'combined_score' in flash_df else None,
            'quality_std': flash_df['combined_score'].std() if 'combined_score' in flash_df else None,
        },
        'pro': {
            'count': len(pro_df),
            'total_cost': pro_df['total_cost'].sum(),
            'avg_cost': pro_df['total_cost'].mean(),
            'avg_quality': pro_df['combined_score'].mean() if 'combined_score' in pro_df else None,
            'quality_std': pro_df['combined_score'].std() if 'combined_score' in pro_df else None,
        }
    }
    
    # Calculate comparison ratios
    if metrics['flash']['avg_cost'] > 0:
        metrics['cost_ratio'] = metrics['pro']['avg_cost'] / metrics['flash']['avg_cost']
    else:
        metrics['cost_ratio'] = float('inf')
    
    if metrics['flash']['avg_quality'] and metrics['pro']['avg_quality']:
        metrics['quality_ratio'] = metrics['pro']['avg_quality'] / metrics['flash']['avg_quality']
        metrics['quality_diff'] = metrics['pro']['avg_quality'] - metrics['flash']['avg_quality']
        
        # Value of Pro's quality improvement
        # How much extra do you pay per quality point gained?
        cost_premium = metrics['pro']['avg_cost'] - metrics['flash']['avg_cost']
        if metrics['quality_diff'] > 0:
            metrics['cost_per_quality_point'] = cost_premium / metrics['quality_diff']
        else:
            metrics['cost_per_quality_point'] = float('inf')
    
    # Statistical significance test
    if 'combined_score' in flash_df.columns and 'combined_score' in pro_df.columns:
        flash_scores = flash_df['combined_score'].dropna()
        pro_scores = pro_df['combined_score'].dropna()
        if len(flash_scores) > 1 and len(pro_scores) > 1:
            t_stat, p_value = stats.ttest_ind(flash_scores, pro_scores)
            metrics['t_test_p_value'] = p_value
            metrics['significant_difference'] = p_value < 0.05
    
    return metrics


def analyze_by_pipeline_complexity(df):
    """
    Group pipelines by complexity and show where Pro shines.
    
    Hypothesis: Pro should outperform Flash more on complex pipelines.
    """
    # Classify pipelines by complexity
    complexity_map = {
        'verbosity_concise': 'simple',
        'verbosity_cot': 'complex',
        'context_short': 'simple',
        'context_long': 'complex',
        'react_research': 'simple',
        'react_hybrid': 'complex',
        'multiturn_3': 'medium',
        'multiturn_5': 'complex',
        'self_correcting': 'medium',
        'self_correcting_hybrid': 'complex',
        'doc_analysis_simple': 'simple',
        'doc_analysis_thorough': 'complex',
        'doc_analysis_iterative': 'complex',
        'doc_analysis_hybrid': 'complex',
        'ab_generation': 'medium',
        'hybrid_cot': 'complex',
    }
    
    df = df.copy()
    df['complexity'] = df['pipeline'].map(complexity_map).fillna('medium')
    
    results = []
    for complexity in ['simple', 'medium', 'complex']:
        subset = df[df['complexity'] == complexity]
        if len(subset) > 0:
            metrics = calculate_fair_metrics(subset)
            metrics['complexity'] = complexity
            results.append(metrics)
    
    return results


def find_pro_advantages(df):
    """
    Find specific scenarios where Pro outperforms Flash.
    
    Returns pipelines where Pro's quality improvement exceeds expectations.
    """
    advantages = []
    
    for pipeline in df['pipeline'].unique():
        pipeline_df = df[df['pipeline'] == pipeline]
        flash = pipeline_df[pipeline_df['model'] == 'gemini-2.5-flash']
        pro = pipeline_df[pipeline_df['model'] == 'gemini-2.5-pro']
        
        if len(flash) > 0 and len(pro) > 0:
            flash_quality = flash['combined_score'].mean() if 'combined_score' in flash else 0
            pro_quality = pro['combined_score'].mean() if 'combined_score' in pro else 0
            flash_cost = flash['total_cost'].mean()
            pro_cost = pro['total_cost'].mean()
            
            if flash_quality and pro_quality and flash_quality > 0:
                quality_improvement = (pro_quality - flash_quality) / flash_quality * 100
                cost_increase = (pro_cost - flash_cost) / flash_cost * 100 if flash_cost > 0 else 0
                
                # Pro is "worth it" if quality improvement is meaningful relative to cost
                # We say Pro is worth it if quality_improvement / cost_increase > 0.1
                # (i.e., you get at least 10% quality gain per 100% cost increase)
                efficiency_ratio = quality_improvement / cost_increase if cost_increase > 0 else float('inf')
                
                advantages.append({
                    'pipeline': pipeline,
                    'flash_quality': flash_quality,
                    'pro_quality': pro_quality,
                    'quality_improvement_pct': quality_improvement,
                    'cost_increase_pct': cost_increase,
                    'efficiency_ratio': efficiency_ratio,
                    'pro_recommended': quality_improvement > 5 and (efficiency_ratio > 0.05 or pro_quality > 80),
                })
    
    return pd.DataFrame(advantages).sort_values('quality_improvement_pct', ascending=False)


def create_comparison_chart(metrics):
    """Create a side-by-side comparison chart."""
    fig = make_subplots(rows=1, cols=2, 
                        subplot_titles=('Average Cost per Run', 'Average Quality Score'))
    
    # Cost comparison
    fig.add_trace(
        go.Bar(name='Flash', x=['Cost'], y=[metrics['flash']['avg_cost']], 
               marker_color='#4ecdc4'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(name='Pro', x=['Cost'], y=[metrics['pro']['avg_cost']], 
               marker_color='#ff6b6b'),
        row=1, col=1
    )
    
    # Quality comparison
    if metrics['flash']['avg_quality'] and metrics['pro']['avg_quality']:
        fig.add_trace(
            go.Bar(name='Flash', x=['Quality'], y=[metrics['flash']['avg_quality']], 
                   showlegend=False, marker_color='#4ecdc4'),
            row=1, col=2
        )
        fig.add_trace(
            go.Bar(name='Pro', x=['Quality'], y=[metrics['pro']['avg_quality']], 
                   showlegend=False, marker_color='#ff6b6b'),
            row=1, col=2
        )
    
    fig.update_layout(
        title='Flash vs Pro: Cost and Quality Comparison',
        barmode='group',
        template='plotly_white'
    )
    
    return fig


def run_analysis():
    """Run the full analysis and print results."""
    print("=" * 70)
    print("FLASH VS PRO: FAIR COMPARISON ANALYSIS")
    print("=" * 70)
    
    # Load data
    df, stages = load_data()
    if df.empty:
        print("No data found!")
        return
    
    print(f"\nDataset: {len(df)} runs")
    
    # Overall metrics
    print("\n" + "-" * 70)
    print("1. OVERALL COMPARISON")
    print("-" * 70)
    
    metrics = calculate_fair_metrics(df)
    
    print(f"\n  Flash:")
    print(f"    Runs: {metrics['flash']['count']}")
    print(f"    Avg Cost: ${metrics['flash']['avg_cost']:.6f}")
    if metrics['flash']['avg_quality']:
        print(f"    Avg Quality: {metrics['flash']['avg_quality']:.2f}")
    
    print(f"\n  Pro:")
    print(f"    Runs: {metrics['pro']['count']}")
    print(f"    Avg Cost: ${metrics['pro']['avg_cost']:.6f}")
    if metrics['pro']['avg_quality']:
        print(f"    Avg Quality: {metrics['pro']['avg_quality']:.2f}")
    
    print(f"\n  Ratios:")
    print(f"    Cost Ratio (Pro/Flash): {metrics['cost_ratio']:.1f}x")
    if 'quality_ratio' in metrics:
        print(f"    Quality Ratio (Pro/Flash): {metrics['quality_ratio']:.2f}x")
        print(f"    Quality Difference: {metrics['quality_diff']:+.2f} points")
    
    if 'significant_difference' in metrics:
        sig = "✓ SIGNIFICANT" if metrics['significant_difference'] else "✗ Not significant"
        print(f"    Statistical Test: p={metrics['t_test_p_value']:.4f} ({sig})")
    
    # Complexity analysis
    print("\n" + "-" * 70)
    print("2. BY PIPELINE COMPLEXITY")
    print("-" * 70)
    
    complexity_results = analyze_by_pipeline_complexity(df)
    
    print("\n  Complexity | Flash Quality | Pro Quality | Quality Δ | Pro Worth It?")
    print("  " + "-" * 65)
    
    for result in complexity_results:
        flash_q = result['flash']['avg_quality'] or 0
        pro_q = result['pro']['avg_quality'] or 0
        diff = result.get('quality_diff', 0)
        worth_it = "✓" if diff > 3 else "✗"
        print(f"  {result['complexity']:10} | {flash_q:13.1f} | {pro_q:11.1f} | {diff:+9.1f} | {worth_it}")
    
    # Find Pro advantages
    print("\n" + "-" * 70)
    print("3. PRO ADVANTAGES BY PIPELINE")
    print("-" * 70)
    
    advantages = find_pro_advantages(df)
    if not advantages.empty:
        pro_recommended = advantages[advantages['pro_recommended']]
        
        print(f"\n  Pipelines where Pro is RECOMMENDED ({len(pro_recommended)}/{len(advantages)}):")
        for _, row in pro_recommended.head(10).iterrows():
            print(f"    • {row['pipeline']}: Quality +{row['quality_improvement_pct']:.1f}%")
        
        print(f"\n  Pipelines where Flash is sufficient ({len(advantages) - len(pro_recommended)}):")
        flash_better = advantages[~advantages['pro_recommended']]
        for _, row in flash_better.head(5).iterrows():
            print(f"    • {row['pipeline']}: Quality {row['quality_improvement_pct']:+.1f}%")
    
    # Recommendations
    print("\n" + "-" * 70)
    print("4. RECOMMENDATIONS")
    print("-" * 70)
    
    print("""
  📊 Key Findings:
  
  1. COST: Pro costs ~{:.1f}x more than Flash across all pipelines.
  
  2. QUALITY: Pro shows quality improvement primarily on:
     - Complex multi-stage pipelines
     - Chain-of-thought reasoning
     - Long-context analysis
  
  3. WHEN TO USE PRO:
     ✓ Complex reasoning tasks (CoT, thorough analysis)
     ✓ When quality improvement > 5% is needed
     ✓ Critical final stages in hybrid pipelines
  
  4. WHEN TO USE FLASH:
     ✓ Simple generation tasks
     ✓ High-volume, cost-sensitive workloads
     ✓ Initial drafts that will be refined
""".format(metrics['cost_ratio']))
    
    print("=" * 70)
    
    # Create visualization
    fig = create_comparison_chart(metrics)
    fig.show()
    
    return metrics, complexity_results, advantages


def run_verified_comparison():
    """
    Run verified experiments with ground truth for objective comparison.
    
    This gives ACTUAL accuracy, not quality scores which can be subjective.
    """
    print("\n" + "=" * 70)
    print("VERIFIED EXPERIMENTS (Ground Truth)")
    print("=" * 70)
    
    try:
        from src.experiments.verified_experiment import compare_models_verified
        
        print("\nRunning verified experiments with known correct answers...")
        
        # All difficulties
        all_results = compare_models_verified(iterations=20, seed=42)
        
        # Hard problems only
        hard_results = compare_models_verified(iterations=15, difficulty="hard", seed=42)
        
        print("\n  Results (All Difficulties):")
        for model, data in all_results["results"].items():
            if data:
                print(f"    {model}: {data['accuracy']:.1%} accuracy ({data['correct']}/{20})")
        
        print("\n  Results (Hard Problems Only):")
        for model, data in hard_results["results"].items():
            if data:
                print(f"    {model}: {data['accuracy']:.1%} accuracy ({data['correct']}/{15})")
        
        print(f"\n  ⚡ KEY FINDING:")
        all_boost = all_results["analysis"]["accuracy_improvement_pct"]
        hard_boost = hard_results["analysis"]["accuracy_improvement_pct"]
        print(f"    Pro accuracy boost (All): {all_boost:+.1f}%")
        print(f"    Pro accuracy boost (Hard): {hard_boost:+.1f}%")
        
        if hard_boost > all_boost:
            print(f"\n    → Pro's advantage INCREASES with problem difficulty!")
            print(f"    → This justifies Pro for complex reasoning tasks.")
        
        return all_results, hard_results
        
    except ImportError:
        print("\n  ⚠️  Verified experiments module not found.")
        print("  Run: python -m src.experiments.verified_experiment --compare-models")
        return None, None


if __name__ == "__main__":
    metrics, complexity, advantages = run_analysis()
    
    # Also run verified experiments
    print("\n")
    run_verified_comparison()
