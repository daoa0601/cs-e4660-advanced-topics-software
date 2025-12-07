"""
Unit tests for cost_calculator module.

Tests cover:
- Basic cost calculation
- Tiered pricing (standard vs long-context)
- Cost breakdown details
- Cost estimation
- Format functions
- Edge cases
"""

import pytest
from src.cost_calculator import (
    calculate_cost,
    calculate_cost_breakdown,
    estimate_cost,
    format_cost,
    get_model_pricing,
    list_models,
)


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_flash_standard_tier(self, flash_pricing):
        """Flash model with standard context should use standard pricing."""
        # 1000 input + 500 output tokens
        # Input: (1000 / 1M) * $0.15 = $0.00015
        # Output: (500 / 1M) * $0.60 = $0.0003
        # Total: $0.00045
        cost = calculate_cost(1000, 500, "flash")
        assert cost == pytest.approx(0.00045, rel=1e-4)

    def test_flash_long_context_tier(self, flash_pricing):
        """Flash model with >200K context should use long-context pricing."""
        # Same tokens but with 250K context
        # Input: (1000 / 1M) * $0.30 = $0.0003
        # Output: (500 / 1M) * $1.20 = $0.0006
        # Total: $0.0009
        cost = calculate_cost(1000, 500, "flash", context_tokens=250_000)
        assert cost == pytest.approx(0.0009, rel=1e-4)

    def test_pro_standard_tier(self, pro_pricing):
        """Pro model with standard context should use standard pricing."""
        # 1000 input + 500 output tokens
        # Input: (1000 / 1M) * $1.25 = $0.00125
        # Output: (500 / 1M) * $10.00 = $0.005
        # Total: $0.00625
        cost = calculate_cost(1000, 500, "pro")
        assert cost == pytest.approx(0.00625, rel=1e-4)

    def test_pro_long_context_tier(self, pro_pricing):
        """Pro model with >200K context should use long-context pricing."""
        # Input: (1000 / 1M) * $2.50 = $0.0025
        # Output: (500 / 1M) * $15.00 = $0.0075
        # Total: $0.01
        cost = calculate_cost(1000, 500, "pro", context_tokens=250_000)
        assert cost == pytest.approx(0.01, rel=1e-4)

    def test_model_aliases(self):
        """Model aliases should work (flash == gemini-2.5-flash)."""
        cost_alias = calculate_cost(1000, 500, "flash")
        cost_full = calculate_cost(1000, 500, "gemini-2.5-flash")
        assert cost_alias == cost_full

    def test_zero_tokens(self):
        """Zero tokens should return zero cost."""
        cost = calculate_cost(0, 0, "flash")
        assert cost == 0.0

    def test_output_only(self):
        """Output-only cost calculation."""
        cost = calculate_cost(0, 1000, "flash")
        # Output: (1000 / 1M) * $0.60 = $0.0006
        assert cost == pytest.approx(0.0006, rel=1e-4)

    def test_precision(self):
        """Cost should have 6 decimal precision."""
        cost = calculate_cost(1, 1, "flash")
        # Very small cost should still be precise
        assert isinstance(cost, float)
        # Should be rounded to 6 decimals
        assert len(str(cost).split(".")[-1]) <= 6

    def test_threshold_boundary_below(self):
        """At exactly 200K tokens, should use standard pricing."""
        cost_at_threshold = calculate_cost(1000, 500, "flash", context_tokens=200_000)
        cost_below_threshold = calculate_cost(1000, 500, "flash", context_tokens=199_999)
        # Both should use standard pricing
        assert cost_at_threshold == cost_below_threshold

    def test_threshold_boundary_above(self):
        """At 200,001 tokens, should use long-context pricing."""
        cost_at_threshold = calculate_cost(1000, 500, "flash", context_tokens=200_000)
        cost_above_threshold = calculate_cost(1000, 500, "flash", context_tokens=200_001)
        # Above should be 2x
        assert cost_above_threshold > cost_at_threshold


class TestCalculateCostBreakdown:
    """Tests for calculate_cost_breakdown function."""

    def test_breakdown_contains_required_fields(self):
        """Breakdown should contain all required fields."""
        breakdown = calculate_cost_breakdown(1000, 500, "flash")
        required_fields = [
            "input_cost",
            "output_cost",
            "total_cost",
            "input_tokens",
            "output_tokens",
            "pricing_tier",
            "context_tokens",
        ]
        for field in required_fields:
            assert field in breakdown, f"Missing field: {field}"

    def test_breakdown_tier_detection(self):
        """Breakdown should correctly identify pricing tier."""
        standard = calculate_cost_breakdown(1000, 500, "flash")
        assert standard["pricing_tier"] == "standard"

        long_context = calculate_cost_breakdown(1000, 500, "flash", context_tokens=250_000)
        assert long_context["pricing_tier"] == "long_context"

    def test_breakdown_totals_match(self):
        """Breakdown total should match individual costs."""
        breakdown = calculate_cost_breakdown(1000, 500, "flash")
        expected_total = breakdown["input_cost"] + breakdown["output_cost"]
        assert breakdown["total_cost"] == pytest.approx(expected_total, rel=1e-6)


class TestEstimateCost:
    """Tests for estimate_cost function."""

    def test_estimate_basic(self):
        """Basic estimation with ~4 chars per token."""
        prompt = "Hello world!"  # 12 chars = ~3 tokens
        cost = estimate_cost(prompt, 100, "flash")
        # Input: (3 / 1M) * $0.15 ≈ negligible
        # Output: (100 / 1M) * $0.60 = $0.00006
        assert cost > 0

    def test_estimate_longer_prompt(self):
        """Longer prompts should cost more."""
        short = estimate_cost("Hi", 100, "flash")
        long = estimate_cost("This is a much longer prompt with many words", 100, "flash")
        assert long > short

    def test_estimate_more_output(self):
        """More expected output should cost more."""
        few = estimate_cost("Test", 100, "flash")
        many = estimate_cost("Test", 1000, "flash")
        assert many > few


class TestFormatCost:
    """Tests for format_cost function."""

    def test_format_tiny_cost(self):
        """Very small costs should show 6 decimals."""
        formatted = format_cost(0.000001)
        assert formatted == "$0.000001"

    def test_format_small_cost(self):
        """Small costs should show 4 decimals."""
        formatted = format_cost(0.0123)
        assert formatted == "$0.0123"

    def test_format_large_cost(self):
        """Costs >= $1 should show 2 decimals."""
        formatted = format_cost(1.5)
        assert formatted == "$1.50"

    def test_format_includes_dollar_sign(self):
        """Formatted cost should include dollar sign."""
        formatted = format_cost(0.5)
        assert formatted.startswith("$")


class TestModelRegistry:
    """Tests for model pricing registry."""

    def test_flash_in_registry(self):
        """Flash model should be in registry."""
        pricing = get_model_pricing("flash")
        assert pricing is not None

    def test_pro_in_registry(self):
        """Pro model should be in registry."""
        pricing = get_model_pricing("pro")
        assert pricing is not None

    def test_list_models_not_empty(self):
        """list_models should return available models."""
        models = list_models()
        assert len(models) > 0
        assert "gemini-2.5-flash" in models or "flash" in str(models)

    def test_unknown_model_raises(self):
        """Unknown model should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown model"):
            calculate_cost(1000, 500, "unknown-model-xyz")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_large_token_counts(self):
        """Very large token counts should work."""
        cost = calculate_cost(1_000_000, 500_000, "flash")
        assert cost > 0

    def test_context_tokens_none(self):
        """None context_tokens should use input_tokens for tier."""
        cost_none = calculate_cost(1000, 500, "flash", context_tokens=None)
        cost_explicit = calculate_cost(1000, 500, "flash", context_tokens=1000)
        assert cost_none == cost_explicit
