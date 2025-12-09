"""
Domain registry and utility functions.

Contains:
- DOMAINS: Registry of all domain configurations
- get_domain(): Get a domain by name
- list_domains(): List all domain names
- generate_experiment_prompts(): Generate prompts for experiments
- save_prompts_to_file(): Save prompts to JSON
- load_prompts_from_file(): Load prompts from JSON
"""

import json
import random
from typing import List, Dict, Any, Optional

from .models import DomainConfig
from .data import (
    CODING_DOMAIN,
    BIOLOGY_DOMAIN,
    LEGAL_DOMAIN,
    CREATIVE_DOMAIN,
    FINANCE_DOMAIN,
    MEDICAL_DOMAIN,
    GENERAL_DOMAIN,
    COMPLEX_REASONING_DOMAIN,
)


# =============================================================================
# DOMAIN REGISTRY
# =============================================================================

DOMAINS: Dict[str, DomainConfig] = {
    "coding": CODING_DOMAIN,
    "biology": BIOLOGY_DOMAIN,
    "legal": LEGAL_DOMAIN,
    "creative": CREATIVE_DOMAIN,
    "finance": FINANCE_DOMAIN,
    "medical": MEDICAL_DOMAIN,
    "general": GENERAL_DOMAIN,
    "complex_reasoning": COMPLEX_REASONING_DOMAIN,
}


def get_domain(name: str) -> Optional[DomainConfig]:
    """Get a domain configuration by name."""
    return DOMAINS.get(name.lower())


def list_domains() -> List[str]:
    """List all available domain names."""
    return list(DOMAINS.keys())


def generate_experiment_prompts(
    domain: str,
    n_prompts: int = 20,
    seed: Optional[int] = None,
    difficulty_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate prompts for an experiment from a specific domain.

    Args:
        domain: The domain name (coding, biology, legal, etc.)
        n_prompts: Number of prompts to generate
        seed: Random seed for reproducibility
        difficulty_filter: Optional filter for difficulty (easy, medium, hard)

    Returns:
        List of prompt dictionaries with metadata
    """
    domain_config = get_domain(domain)
    if domain_config is None:
        raise ValueError(f"Unknown domain: {domain}. Available: {list_domains()}")

    if difficulty_filter:
        # Filter templates by difficulty
        filtered_templates = [
            t for t in domain_config.templates
            if t.difficulty == difficulty_filter
        ]
        if not filtered_templates:
            raise ValueError(f"No templates with difficulty '{difficulty_filter}' in domain '{domain}'")

        # Create temporary domain config with filtered templates
        filtered_domain = DomainConfig(
            name=domain_config.name,
            description=domain_config.description,
            templates=filtered_templates,
            system_prompts=domain_config.system_prompts,
            evaluation_criteria=domain_config.evaluation_criteria
        )
        return filtered_domain.generate_prompts(n_prompts, seed)

    return domain_config.generate_prompts(n_prompts, seed)


def save_prompts_to_file(prompts: List[Dict[str, Any]], filepath: str) -> None:
    """Save generated prompts to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(prompts, f, indent=2)


def load_prompts_from_file(filepath: str) -> List[Dict[str, Any]]:
    """Load prompts from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)
