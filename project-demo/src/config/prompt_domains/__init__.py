"""
Prompt Template System for Domain-Specific LLM Cost Experiments

This module provides a flexible template system for generating domain-specific
prompts and test inputs for LLM cost analysis experiments.

Supported domains:
- coding: Software development, debugging, code review
- biology: Molecular biology, genetics, biochemistry
- legal: Contract analysis, compliance, legal research
- creative: Writing, storytelling, content creation
- finance: Financial analysis, trading, risk assessment
- medical: Clinical reasoning, diagnosis, treatment planning
- general: General knowledge and reasoning tasks
- complex_reasoning: Multi-step reasoning, proofs, algorithm design
"""

from .models import PromptTemplate, DomainConfig
from .data import (
    # Domain configurations
    CODING_DOMAIN,
    BIOLOGY_DOMAIN,
    LEGAL_DOMAIN,
    CREATIVE_DOMAIN,
    FINANCE_DOMAIN,
    MEDICAL_DOMAIN,
    GENERAL_DOMAIN,
    COMPLEX_REASONING_DOMAIN,
    # Template lists (for direct access)
    CODING_TEMPLATES,
    BIOLOGY_TEMPLATES,
    LEGAL_TEMPLATES,
    CREATIVE_TEMPLATES,
    FINANCE_TEMPLATES,
    MEDICAL_TEMPLATES,
    GENERAL_TEMPLATES,
    COMPLEX_REASONING_TEMPLATES,
)
from .registry import (
    DOMAINS,
    get_domain,
    list_domains,
    generate_experiment_prompts,
    save_prompts_to_file,
    load_prompts_from_file,
)
from .cli import main

__all__ = [
    # Models
    "PromptTemplate",
    "DomainConfig",
    # Domain configurations
    "CODING_DOMAIN",
    "BIOLOGY_DOMAIN",
    "LEGAL_DOMAIN",
    "CREATIVE_DOMAIN",
    "FINANCE_DOMAIN",
    "MEDICAL_DOMAIN",
    "GENERAL_DOMAIN",
    "COMPLEX_REASONING_DOMAIN",
    # Template lists
    "CODING_TEMPLATES",
    "BIOLOGY_TEMPLATES",
    "LEGAL_TEMPLATES",
    "CREATIVE_TEMPLATES",
    "FINANCE_TEMPLATES",
    "MEDICAL_TEMPLATES",
    "GENERAL_TEMPLATES",
    "COMPLEX_REASONING_TEMPLATES",
    # Registry
    "DOMAINS",
    "get_domain",
    "list_domains",
    "generate_experiment_prompts",
    "save_prompts_to_file",
    "load_prompts_from_file",
    # CLI
    "main",
]
