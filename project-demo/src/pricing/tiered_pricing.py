"""
Tiered Token Pricing Configuration for LLM Cost Analysis

This module provides accurate cost calculation that accounts for:
1. Different input/output token rates
2. Long-context pricing tiers (>200K tokens for Gemini 2.5)
3. Multiple model support with easy extension

Pricing tiers (Gemini 2.5):
- Standard: ≤200K context tokens
- Long Context: >200K context tokens

Pricing updated: December 2025
Source: https://cloud.google.com/vertex-ai/generative-ai/pricing
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


class PricingTier(Enum):
    """Pricing tier based on context length."""
    STANDARD = "standard"
    LONG_CONTEXT = "long_context"


@dataclass
class TokenPricing:
    """Pricing configuration for a specific tier."""
    input_price_per_million: float
    output_price_per_million: float
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate total cost for given token counts."""
        input_cost = (input_tokens / 1_000_000) * self.input_price_per_million
        output_cost = (output_tokens / 1_000_000) * self.output_price_per_million
        return input_cost + output_cost
    
    def calculate_cost_breakdown(
        self, input_tokens: int, output_tokens: int
    ) -> Dict[str, float]:
        """Calculate cost with detailed breakdown."""
        input_cost = (input_tokens / 1_000_000) * self.input_price_per_million
        output_cost = (output_tokens / 1_000_000) * self.output_price_per_million
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }


@dataclass
class ModelPricing:
    """Complete pricing configuration for a model with tier support."""
    model_name: str
    model_id: str
    standard: TokenPricing
    long_context: TokenPricing
    context_threshold: int = 200_000  # Gemini 2.5 uses 200K threshold
    
    def get_tier(self, total_context_tokens: int) -> PricingTier:
        """Determine pricing tier based on context length."""
        if total_context_tokens > self.context_threshold:
            return PricingTier.LONG_CONTEXT
        return PricingTier.STANDARD
    
    def get_pricing(self, total_context_tokens: int) -> TokenPricing:
        """Get the appropriate pricing based on context length."""
        tier = self.get_tier(total_context_tokens)
        return self.long_context if tier == PricingTier.LONG_CONTEXT else self.standard
    
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        context_tokens: Optional[int] = None
    ) -> float:
        """
        Calculate cost with automatic tier detection.
        
        Args:
            input_tokens: Number of input tokens for this request
            output_tokens: Number of output tokens for this request
            context_tokens: Total context window size (if different from input_tokens)
                          Used to determine pricing tier for conversation contexts
        """
        # Use input_tokens as context size if not specified
        total_context = context_tokens if context_tokens is not None else input_tokens
        pricing = self.get_pricing(total_context)
        return pricing.calculate_cost(input_tokens, output_tokens)
    
    def calculate_cost_detailed(
        self,
        input_tokens: int,
        output_tokens: int,
        context_tokens: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Calculate cost with detailed breakdown including tier info.
        """
        total_context = context_tokens if context_tokens is not None else input_tokens
        tier = self.get_tier(total_context)
        pricing = self.get_pricing(total_context)
        
        breakdown = pricing.calculate_cost_breakdown(input_tokens, output_tokens)
        breakdown.update({
            "model": self.model_name,
            "model_id": self.model_id,
            "pricing_tier": tier.value,
            "context_tokens": total_context,
            "threshold": self.context_threshold,
            "input_rate": pricing.input_price_per_million,
            "output_rate": pricing.output_price_per_million,
        })
        return breakdown


# =============================================================================
# GOOGLE GEMINI PRICING (December 2025)
# Source: https://cloud.google.com/vertex-ai/generative-ai/pricing
# =============================================================================

GEMINI_FLASH_PRICING = ModelPricing(
    model_name="Gemini 2.5 Flash",
    model_id="gemini-2.5-flash",
    standard=TokenPricing(
        input_price_per_million=0.15,
        output_price_per_million=0.60,
    ),
    long_context=TokenPricing(
        input_price_per_million=0.30,  # 2x standard for >200K tokens
        output_price_per_million=1.20,
    ),
    context_threshold=200_000,
)

GEMINI_PRO_PRICING = ModelPricing(
    model_name="Gemini 2.5 Pro",
    model_id="gemini-2.5-pro",
    standard=TokenPricing(
        input_price_per_million=1.25,
        output_price_per_million=10.00,  # Includes thinking tokens
    ),
    long_context=TokenPricing(
        input_price_per_million=2.50,  # 2x standard for >200K tokens
        output_price_per_million=15.00,
    ),
    context_threshold=200_000,
)


# =============================================================================
# OPENAI PRICING (for reference/future support)
# =============================================================================

GPT4_TURBO_PRICING = ModelPricing(
    model_name="GPT-4 Turbo",
    model_id="gpt-4-turbo",
    standard=TokenPricing(
        input_price_per_million=10.00,
        output_price_per_million=30.00,
    ),
    long_context=TokenPricing(
        input_price_per_million=10.00,
        output_price_per_million=30.00,
    ),
    context_threshold=128_000,
)

GPT4O_PRICING = ModelPricing(
    model_name="GPT-4o",
    model_id="gpt-4o",
    standard=TokenPricing(
        input_price_per_million=2.50,
        output_price_per_million=10.00,
    ),
    long_context=TokenPricing(
        input_price_per_million=2.50,
        output_price_per_million=10.00,
    ),
    context_threshold=128_000,
)

GPT4O_MINI_PRICING = ModelPricing(
    model_name="GPT-4o Mini",
    model_id="gpt-4o-mini",
    standard=TokenPricing(
        input_price_per_million=0.15,
        output_price_per_million=0.60,
    ),
    long_context=TokenPricing(
        input_price_per_million=0.15,
        output_price_per_million=0.60,
    ),
    context_threshold=128_000,
)


# =============================================================================
# ANTHROPIC PRICING (for reference/future support)
# =============================================================================

CLAUDE_SONNET_PRICING = ModelPricing(
    model_name="Claude 3.5 Sonnet",
    model_id="claude-3-5-sonnet-20241022",
    standard=TokenPricing(
        input_price_per_million=3.00,
        output_price_per_million=15.00,
    ),
    long_context=TokenPricing(
        input_price_per_million=3.00,
        output_price_per_million=15.00,
    ),
    context_threshold=200_000,
)

CLAUDE_HAIKU_PRICING = ModelPricing(
    model_name="Claude 3.5 Haiku",
    model_id="claude-3-5-haiku-20241022",
    standard=TokenPricing(
        input_price_per_million=0.80,
        output_price_per_million=4.00,
    ),
    long_context=TokenPricing(
        input_price_per_million=0.80,
        output_price_per_million=4.00,
    ),
    context_threshold=200_000,
)


# =============================================================================
# MODEL REGISTRY
# =============================================================================

MODEL_PRICING: Dict[str, ModelPricing] = {
    # Gemini models (primary)
    "gemini-2.5-flash": GEMINI_FLASH_PRICING,
    "flash": GEMINI_FLASH_PRICING,
    
    "gemini-2.5-pro": GEMINI_PRO_PRICING,
    "pro": GEMINI_PRO_PRICING,
    
    # OpenAI models (reference)
    "gpt-4-turbo": GPT4_TURBO_PRICING,
    "gpt-4o": GPT4O_PRICING,
    "gpt-4o-mini": GPT4O_MINI_PRICING,
    
    # Anthropic models (reference)
    "claude-3-5-sonnet": CLAUDE_SONNET_PRICING,
    "claude-3-5-sonnet-20241022": CLAUDE_SONNET_PRICING,
    "claude-3-5-haiku": CLAUDE_HAIKU_PRICING,
    "claude-3-5-haiku-20241022": CLAUDE_HAIKU_PRICING,
}


def get_model_pricing(model_id: str) -> Optional[ModelPricing]:
    """Get pricing configuration for a model."""
    # Try exact match first
    if model_id in MODEL_PRICING:
        return MODEL_PRICING[model_id]
    
    # Try partial match
    model_lower = model_id.lower()
    for key, pricing in MODEL_PRICING.items():
        if key.lower() in model_lower or model_lower in key.lower():
            return pricing
    
    return None


def calculate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    context_tokens: Optional[int] = None
) -> float:
    """
    Calculate cost for a model request with automatic tier detection.
    
    Args:
        model_id: The model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        context_tokens: Total context size (for tier determination)
    
    Returns:
        Total cost in dollars
    
    Raises:
        ValueError: If model is not found in pricing registry
    """
    pricing = get_model_pricing(model_id)
    if pricing is None:
        raise ValueError(
            f"Unknown model: {model_id}. "
            f"Available models: {list(MODEL_PRICING.keys())}"
        )
    
    return pricing.calculate_cost(input_tokens, output_tokens, context_tokens)


def calculate_cost_detailed(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    context_tokens: Optional[int] = None
) -> Dict[str, any]:
    """
    Calculate cost with detailed breakdown.
    
    Returns dictionary with:
        - input_cost, output_cost, total_cost
        - input_tokens, output_tokens, context_tokens
        - model, model_id, pricing_tier
        - input_rate, output_rate, threshold
    """
    pricing = get_model_pricing(model_id)
    if pricing is None:
        raise ValueError(f"Unknown model: {model_id}")
    
    return pricing.calculate_cost_detailed(input_tokens, output_tokens, context_tokens)


def list_models() -> Dict[str, str]:
    """List all available models with their names."""
    seen = set()
    models = {}
    for key, pricing in MODEL_PRICING.items():
        if pricing.model_id not in seen:
            models[pricing.model_id] = pricing.model_name
            seen.add(pricing.model_id)
    return models


# =============================================================================
# COST TRACKER CLASS (for integration with existing system)
# =============================================================================

class TieredCostTracker:
    """
    Track costs across multiple requests with tier-aware pricing.
    
    Designed for integration with the existing LLM cost analysis platform.
    """
    
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.pricing = get_model_pricing(model_id)
        if self.pricing is None:
            raise ValueError(f"Unknown model: {model_id}")
        
        self.requests: list = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.long_context_requests = 0
    
    def add_request(
        self,
        input_tokens: int,
        output_tokens: int,
        context_tokens: Optional[int] = None,
        stage_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Record a request and calculate its cost.
        
        Returns detailed cost breakdown for this request.
        """
        breakdown = self.pricing.calculate_cost_detailed(
            input_tokens, output_tokens, context_tokens
        )
        
        # Track aggregates
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += breakdown["total_cost"]
        
        if breakdown["pricing_tier"] == "long_context":
            self.long_context_requests += 1
        
        # Store request details
        request_record = {
            **breakdown,
            "stage_name": stage_name,
            "metadata": metadata or {},
        }
        self.requests.append(request_record)
        
        return breakdown
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary statistics for all tracked requests."""
        return {
            "model": self.pricing.model_name,
            "model_id": self.model_id,
            "total_requests": len(self.requests),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": self.total_cost,
            "long_context_requests": self.long_context_requests,
            "long_context_percentage": (
                self.long_context_requests / len(self.requests) * 100
                if self.requests else 0
            ),
            "avg_cost_per_request": (
                self.total_cost / len(self.requests) if self.requests else 0
            ),
        }
    
    def get_cost_by_stage(self) -> Dict[str, float]:
        """Get cost breakdown by stage name."""
        stage_costs = {}
        for req in self.requests:
            stage = req.get("stage_name", "unknown")
            stage_costs[stage] = stage_costs.get(stage, 0) + req["total_cost"]
        return stage_costs


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Calculate LLM costs with tiered pricing"
    )
    parser.add_argument("--model", "-m", help="Model ID")
    parser.add_argument("--input-tokens", "-i", type=int, help="Input token count")
    parser.add_argument("--output-tokens", "-o", type=int, help="Output token count")
    parser.add_argument("--context-tokens", "-c", type=int, default=None,
                       help="Total context size (for tier determination)")
    parser.add_argument("--list-models", action="store_true",
                       help="List available models")
    
    args = parser.parse_args()
    
    if args.list_models:
        print("\nAvailable Models and Pricing:\n")
        print("-" * 80)
        for model_id, name in list_models().items():
            pricing = get_model_pricing(model_id)
            print(f"\n{name} ({model_id})")
            print(f"  Standard (≤{pricing.context_threshold:,} tokens):")
            print(f"    Input:  ${pricing.standard.input_price_per_million:.2f}/1M tokens")
            print(f"    Output: ${pricing.standard.output_price_per_million:.2f}/1M tokens")
            print(f"  Long Context (>{pricing.context_threshold:,} tokens):")
            print(f"    Input:  ${pricing.long_context.input_price_per_million:.2f}/1M tokens")
            print(f"    Output: ${pricing.long_context.output_price_per_million:.2f}/1M tokens")
        exit(0)
    
    # Validate required args for cost calculation
    if not args.model or args.input_tokens is None or args.output_tokens is None:
        parser.error(
            "--model, --input-tokens, and --output-tokens are required "
            "for cost calculation"
        )
    
    # Calculate cost
    try:
        breakdown = calculate_cost_detailed(
            args.model,
            args.input_tokens,
            args.output_tokens,
            args.context_tokens
        )
        
        print(f"\n{'='*50}")
        print(f"Cost Calculation for {breakdown['model']}")
        print(f"{'='*50}")
        print(f"Model ID:        {breakdown['model_id']}")
        print(f"Pricing Tier:    {breakdown['pricing_tier']}")
        print(f"Context Tokens:  {breakdown['context_tokens']:,}")
        print(f"Tier Threshold:  {breakdown['threshold']:,}")
        print(f"\nToken Counts:")
        print(f"  Input:         {breakdown['input_tokens']:,}")
        print(f"  Output:        {breakdown['output_tokens']:,}")
        print(f"\nPricing Rates:")
        print(f"  Input Rate:    ${breakdown['input_rate']:.2f}/1M tokens")
        print(f"  Output Rate:   ${breakdown['output_rate']:.2f}/1M tokens")
        print(f"\nCosts:")
        print(f"  Input Cost:    ${breakdown['input_cost']:.6f}")
        print(f"  Output Cost:   ${breakdown['output_cost']:.6f}")
        print(f"  Total Cost:    ${breakdown['total_cost']:.6f}")
        print(f"{'='*50}\n")
        
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
