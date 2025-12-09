"""
Vulnerability query functions.

Contains:
- get_vulnerabilities(): Get ground truth for a document
- get_vulnerability_ids(): Get vulnerability IDs
- count_by_severity(): Count by severity
- get_all_document_ids(): List all documents
- calculate_detection_score(): Score detection accuracy
"""

from typing import List, Dict

from .models import Severity, DocumentVulnerabilities


def get_vulnerabilities(document_id: str, vulnerabilities_dict: Dict[str, DocumentVulnerabilities]) -> DocumentVulnerabilities:
    """Get vulnerability ground truth for a document."""
    if document_id not in vulnerabilities_dict:
        raise ValueError(f"Unknown document ID: {document_id}")
    return vulnerabilities_dict[document_id]


def get_vulnerability_ids(document_id: str, vulnerabilities_dict: Dict[str, DocumentVulnerabilities]) -> List[str]:
    """Get list of vulnerability IDs for a document."""
    return [v.id for v in get_vulnerabilities(document_id, vulnerabilities_dict).vulnerabilities]


def count_by_severity(document_id: str, vulnerabilities_dict: Dict[str, DocumentVulnerabilities]) -> Dict[str, int]:
    """Count vulnerabilities by severity for a document."""
    vulns = get_vulnerabilities(document_id, vulnerabilities_dict)
    counts = {s.value: 0 for s in Severity}
    for v in vulns.vulnerabilities:
        counts[v.severity.value] += 1
    return counts


def get_all_document_ids(vulnerabilities_dict: Dict[str, DocumentVulnerabilities]) -> List[str]:
    """Get list of all document IDs with ground truth."""
    return list(vulnerabilities_dict.keys())


def calculate_detection_score(
    document_id: str,
    detected_issues: List[str],
    vulnerabilities_dict: Dict[str, DocumentVulnerabilities],
    partial_match_weight: float = 0.5,
) -> Dict[str, float]:
    """
    Calculate how well detected issues match ground truth.

    Args:
        document_id: ID of the document analyzed
        detected_issues: List of issue descriptions from the model
        vulnerabilities_dict: The VULNERABILITIES dictionary
        partial_match_weight: Weight for partial matches (0-1)

    Returns:
        Dictionary with precision, recall, and F1 score
    """
    ground_truth = get_vulnerabilities(document_id, vulnerabilities_dict)

    # Simple keyword matching (could be improved with embeddings)
    gt_keywords = []
    for v in ground_truth.vulnerabilities:
        keywords = set()
        keywords.update(v.title.lower().split())
        keywords.update(v.category.lower().split())
        keywords.update(v.description.lower().split())
        gt_keywords.append((v.id, keywords))

    detected_lower = [d.lower() for d in detected_issues]

    # Count matches
    matched_gt = set()
    matched_detected = set()

    for i, detected in enumerate(detected_lower):
        detected_words = set(detected.split())
        for gt_id, gt_kw in gt_keywords:
            overlap = len(detected_words & gt_kw)
            if overlap >= 3:  # Threshold for match
                matched_gt.add(gt_id)
                matched_detected.add(i)

    true_positives = len(matched_gt)
    total_gt = len(ground_truth.vulnerabilities)
    total_detected = len(detected_issues)

    precision = true_positives / total_detected if total_detected > 0 else 0
    recall = true_positives / total_gt if total_gt > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "true_positives": true_positives,
        "total_ground_truth": total_gt,
        "total_detected": total_detected,
    }
