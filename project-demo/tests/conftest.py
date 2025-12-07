"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_tokens():
    """Sample token counts for testing."""
    return {
        "small": {"input": 100, "output": 50},
        "medium": {"input": 1000, "output": 500},
        "large": {"input": 10000, "output": 5000},
        "long_context": {"input": 250000, "output": 1000},
    }


@pytest.fixture
def flash_pricing():
    """Expected Flash pricing rates."""
    return {
        "standard": {"input_per_1m": 0.15, "output_per_1m": 0.60},
        "long_context": {"input_per_1m": 0.30, "output_per_1m": 1.20},
        "threshold": 200_000,
    }


@pytest.fixture
def pro_pricing():
    """Expected Pro pricing rates."""
    return {
        "standard": {"input_per_1m": 1.25, "output_per_1m": 10.00},
        "long_context": {"input_per_1m": 2.50, "output_per_1m": 15.00},
        "threshold": 200_000,
    }
