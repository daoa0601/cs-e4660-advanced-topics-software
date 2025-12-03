"""
Cost calculation utilities.
"""

from .config import get_pricing


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Calculate the total cost for a model call.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier
    
    Returns:
        Total cost in USD (6 decimal precision)
    """
    pricing = get_pricing(model)
    
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    
    total_cost = input_cost + output_cost
    
    return round(total_cost, 6)


def calculate_cost_breakdown(input_tokens: int, output_tokens: int, model: str) -> dict:
    """
    Calculate detailed cost breakdown for a model call.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier
    
    Returns:
        Dictionary with input_cost, output_cost, and total_cost
    """
    pricing = get_pricing(model)
    
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    total_cost = input_cost + output_cost
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6),
        "model": model,
        "pricing": pricing,
    }


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


if __name__ == "__main__":
    # Example usage
    print("Cost calculation examples:\n")
    
    for model in ["flash", "pro"]:
        breakdown = calculate_cost_breakdown(1000, 500, model)
        print(f"Model: {model}")
        print(f"  Input: {breakdown['input_tokens']} tokens = {format_cost(breakdown['input_cost'])}")
        print(f"  Output: {breakdown['output_tokens']} tokens = {format_cost(breakdown['output_cost'])}")
        print(f"  Total: {format_cost(breakdown['total_cost'])}")
        print()
