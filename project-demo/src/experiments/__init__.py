"""
Experiment runners module.
"""

from .ab_testing import (
    ABTestResult,
    run_ab_test,
    run_ab_test_by_name,
    run_custom_ab_test,
    print_ab_test_analysis,
    list_ab_tests,
)

from .domain_experiment import (
    ExperimentConfig,
    DomainExperimentRunner,
    compare_models_on_domain,
    run_pro_advantage_analysis,
    StageResult,
    RunResult,
)

from .verified_experiment import (
    VerifiedExperimentConfig,
    VerifiedExperimentRunner,
    VerifiedResult,
    compare_models_verified,
    run_verified_comparison_report,
)

from .token_profiler import (
    TokenDistribution,
    TokenProfile,
    run_token_profiler,
    profile_all_workflows,
    generate_summary_table,
    analyze_token_patterns,
)

from .cost_quality_analysis import (
    ParetoPoint,
    CostQualityAnalysis,
    run_cost_quality_analysis,
    calculate_pareto_frontier,
    score_quality_efficiency,
    rank_pipelines_by_efficiency,
)

__all__ = [
    # A/B Testing
    "ABTestResult",
    "run_ab_test",
    "run_ab_test_by_name",
    "run_custom_ab_test",
    "print_ab_test_analysis",
    "list_ab_tests",
    # Domain Experiments
    "ExperimentConfig",
    "DomainExperimentRunner",
    "compare_models_on_domain",
    "run_pro_advantage_analysis",
    "StageResult",
    "RunResult",
    # Verified Experiments (with ground truth)
    "VerifiedExperimentConfig",
    "VerifiedExperimentRunner",
    "VerifiedResult",
    "compare_models_verified",
    "run_verified_comparison_report",
    # Token Distribution Profiler
    "TokenDistribution",
    "TokenProfile",
    "run_token_profiler",
    "profile_all_workflows",
    "generate_summary_table",
    "analyze_token_patterns",
    # Cost-Quality Analysis
    "ParetoPoint",
    "CostQualityAnalysis",
    "run_cost_quality_analysis",
    "calculate_pareto_frontier",
    "score_quality_efficiency",
    "rank_pipelines_by_efficiency",
]
