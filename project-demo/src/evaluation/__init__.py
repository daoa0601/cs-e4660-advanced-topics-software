"""
Evaluation module for quality assessment.
"""

from .automated import (
    QualityScore,
    evaluate_automated,
    evaluate_with_llm,
    evaluate_cost_quality_ratio,
    CostQualityAnalysis,
    analyze_cost_quality,
)

from .vulnerability_ground_truth import (
    Severity,
    Vulnerability,
    DocumentVulnerabilities,
    VULNERABILITIES,
    get_vulnerabilities,
    get_vulnerability_ids,
    count_by_severity,
    get_all_document_ids,
    calculate_detection_score,
)

__all__ = [
    # Quality evaluation
    "QualityScore",
    "evaluate_automated",
    "evaluate_with_llm",
    "evaluate_cost_quality_ratio",
    "CostQualityAnalysis",
    "analyze_cost_quality",
    # Vulnerability ground truth
    "Severity",
    "Vulnerability",
    "DocumentVulnerabilities",
    "VULNERABILITIES",
    "get_vulnerabilities",
    "get_vulnerability_ids",
    "count_by_severity",
    "get_all_document_ids",
    "calculate_detection_score",
]
