"""
Model configuration and pricing.
"""

import os
from typing import Dict

# GCP Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# Model pricing per 1M tokens (as of Jan 2025)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gemini-2.5-flash": {
        "input_per_1m": 0.15,
        "output_per_1m": 0.60,
    },
    "gemini-2.5-pro": {
        "input_per_1m": 1.25,
        "output_per_1m": 5.00,
    },
}

# Model ID mappings (short name -> full ID)
MODEL_IDS: Dict[str, str] = {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.5-pro": "gemini-2.5-pro",
}


def get_model_id(model: str) -> str:
    """Convert short model name to full model ID."""
    return MODEL_IDS.get(model, model)


def get_pricing(model: str) -> Dict[str, float]:
    """Get pricing for a model."""
    model_key = model if model in MODEL_PRICING else get_model_id(model)
    return MODEL_PRICING.get(model_key, MODEL_PRICING["gemini-2.5-flash"])
