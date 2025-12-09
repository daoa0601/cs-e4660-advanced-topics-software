"""
Vulnerability Ground Truth Reference

This module contains the expected vulnerabilities for each test document.
Used by the evaluator LLM to score analysis accuracy.

DO NOT include this file in prompts sent to the model being tested.
"""

from typing import List, Dict

from .models import Severity, Vulnerability, DocumentVulnerabilities
from .data import VULNERABILITIES
from .queries import (
    get_vulnerabilities as _get_vulnerabilities,
    get_vulnerability_ids as _get_vulnerability_ids,
    count_by_severity as _count_by_severity,
    get_all_document_ids as _get_all_document_ids,
    calculate_detection_score as _calculate_detection_score,
)


# Wrapper functions that use the global VULNERABILITIES dict
def get_vulnerabilities(document_id: str) -> DocumentVulnerabilities:
    """Get vulnerability ground truth for a document."""
    return _get_vulnerabilities(document_id, VULNERABILITIES)


def get_vulnerability_ids(document_id: str) -> List[str]:
    """Get list of vulnerability IDs for a document."""
    return _get_vulnerability_ids(document_id, VULNERABILITIES)


def count_by_severity(document_id: str) -> Dict[str, int]:
    """Count vulnerabilities by severity for a document."""
    return _count_by_severity(document_id, VULNERABILITIES)


def get_all_document_ids() -> List[str]:
    """Get list of all document IDs with ground truth."""
    return _get_all_document_ids(VULNERABILITIES)


def calculate_detection_score(
    document_id: str,
    detected_issues: List[str],
    partial_match_weight: float = 0.5,
) -> Dict[str, float]:
    """Calculate how well detected issues match ground truth."""
    return _calculate_detection_score(document_id, detected_issues, VULNERABILITIES, partial_match_weight)


__all__ = [
    # Models
    "Severity",
    "Vulnerability",
    "DocumentVulnerabilities",
    # Data
    "VULNERABILITIES",
    # Functions
    "get_vulnerabilities",
    "get_vulnerability_ids",
    "count_by_severity",
    "get_all_document_ids",
    "calculate_detection_score",
]
