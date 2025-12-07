"""
Cost calculation utilities with tiered pricing support.

This module wraps the tiered pricing engine to provide backward-compatible
cost calculation while supporting context-aware pricing tiers.

Pricing tiers (Gemini 2.5):
- Standard: ≤200K context tokens
- Long Context: >200K context tokens (2x pricing)
"""

from typing import Optional

from .pricing.tiered_pricing import (
    calculate_cost as _tiered_calculate_cost,
    calculate_cost_detailed as _tiered_calculate_cost_detailed,
    get_model_pricing,
    TieredCostTracker,
    list_models,
)


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
    context_tokens: Optional[int] = None
) -> float:
    """
    Calculate the total cost for a model call with tiered pricing support.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier (e.g., "flash", "pro", "gemini-2.5-flash")
        context_tokens: Total context size for tier determination (optional).
                       If not provided, input_tokens is used for tier detection.

    Returns:
        Total cost in USD (6 decimal precision)

    Note:
        - Context ≤200K tokens: Standard pricing
        - Context >200K tokens: Long-context pricing (2x rates)
    """
    return round(
        _tiered_calculate_cost(model, input_tokens, output_tokens, context_tokens),
        6
    )


def calculate_cost_breakdown(
    input_tokens: int,
    output_tokens: int,
    model: str,
    context_tokens: Optional[int] = None
) -> dict:
    """
    Calculate detailed cost breakdown for a model call.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier
        context_tokens: Total context size for tier determination

    Returns:
        Dictionary with input_cost, output_cost, total_cost, pricing_tier, etc.
    """
    return _tiered_calculate_cost_detailed(model, input_tokens, output_tokens, context_tokens)


def estimate_cost(prompt: str, expected_output_tokens: int, model: str) -> float:
    """
    Estimate cost before making a call (rough approximation).

    Uses ~4 characters per token as a rough estimate for input.

    Args:
        prompt: The input prompt
        expected_output_tokens: Estimated output tokens
        model: Model identifier

    Returns:
        Estimated total cost in USD
    """
    # Rough estimate: ~4 characters per token
    estimated_input_tokens = len(prompt) // 4
    return calculate_cost(estimated_input_tokens, expected_output_tokens, model)


def format_cost(cost: float) -> str:
    """Format cost for display."""
    if cost < 0.01:
        return f"${cost:.6f}"
    elif cost < 1:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"


# Re-export tiered pricing utilities for advanced usage
__all__ = [
    "calculate_cost",
    "calculate_cost_breakdown",
    "estimate_cost",
    "format_cost",
    "get_model_pricing",
    "TieredCostTracker",
    "list_models",
]


if __name__ == "__main__":
    # Example usage demonstrating tiered pricing
    print("Cost calculation examples (with tiered pricing):\n")

    for model in ["flash", "pro"]:
        print(f"Model: {model}")

        # Standard tier (< 200K context)
        breakdown = calculate_cost_breakdown(1000, 500, model)
        print(f"  Standard tier ({breakdown['context_tokens']:,} context tokens):")
        print(f"    Input: {breakdown['input_tokens']} tokens = ${breakdown['input_cost']:.6f}")
        print(f"    Output: {breakdown['output_tokens']} tokens = ${breakdown['output_cost']:.6f}")
        print(f"    Total: {format_cost(breakdown['total_cost'])}")
        print(f"    Tier: {breakdown['pricing_tier']}")

        # Long-context tier (> 200K context)
        breakdown_long = calculate_cost_breakdown(1000, 500, model, context_tokens=250_000)
        print(f"  Long-context tier ({breakdown_long['context_tokens']:,} context tokens):")
        print(f"    Input: {breakdown_long['input_tokens']} tokens = ${breakdown_long['input_cost']:.6f}")
        print(f"    Output: {breakdown_long['output_tokens']} tokens = ${breakdown_long['output_cost']:.6f}")
        print(f"    Total: {format_cost(breakdown_long['total_cost'])}")
        print(f"    Tier: {breakdown_long['pricing_tier']}")
        print()
