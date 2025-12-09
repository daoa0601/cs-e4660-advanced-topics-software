"""
Vulnerability data models.

Contains:
- Severity enum
- Vulnerability dataclass
- DocumentVulnerabilities dataclass
"""

from dataclasses import dataclass
from typing import List
from enum import Enum


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Vulnerability:
    """A single vulnerability finding."""
    id: str
    title: str
    severity: Severity
    category: str
    description: str
    location: str  # Line number, function name, or section
    cwe_id: str = ""  # Common Weakness Enumeration ID
    remediation: str = ""


@dataclass
class DocumentVulnerabilities:
    """All vulnerabilities for a document."""
    document_id: str
    document_name: str
    vulnerabilities: List[Vulnerability]

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.vulnerabilities if v.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for v in self.vulnerabilities if v.severity == Severity.HIGH)

    @property
    def total_count(self) -> int:
        return len(self.vulnerabilities)
