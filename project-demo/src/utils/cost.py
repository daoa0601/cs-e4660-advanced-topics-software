"""
Cost calculation utilities.
"""

from ..config import get_pricing, get_model_id


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Calculate the cost for a model call.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name (short or full)
    
    Returns:
        Cost in USD
    """
    pricing = get_pricing(model)
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    return input_cost + output_cost


def format_cost(cost: float) -> str:
    """Format cost for display."""
    if cost < 0.01:
        return f"${cost:.6f}"
    elif cost < 1:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
    num_calls: int = 1,
) -> dict:
    """
    Estimate cost for multiple calls.
    
    Returns:
        Dictionary with cost breakdown
    """
    pricing = get_pricing(model)
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"] * num_calls
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"] * num_calls
    total = input_cost + output_cost
    
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total,
        "formatted": format_cost(total),
        "per_call": format_cost(total / num_calls) if num_calls > 0 else "$0.00",
    }
