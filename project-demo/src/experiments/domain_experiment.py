"""
Domain Experiment Runner for LLM Cost Analysis

This module provides a unified interface for running domain-specific
LLM cost experiments with accurate tiered pricing.

Key features:
- Domain-specific prompt generation (coding, biology, legal, etc.)
- Tiered token pricing (standard vs long-context)
- Integration with existing experiment framework
- Comprehensive cost tracking and reporting

Usage:
    python -m src.experiments.domain_experiment --domain coding --iterations 20
    python -m src.experiments.domain_experiment --domain biology --difficulty hard
    python -m src.experiments.domain_experiment --list-domains
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Import from our modules
from ..config.prompt_templates import (
    DOMAINS,
    get_domain,
    list_domains,
    generate_experiment_prompts,
    DomainConfig,
)
from ..pricing.tiered_pricing import (
    calculate_cost,
    calculate_cost_detailed,
    get_model_pricing,
    TieredCostTracker,
    MODEL_PRICING,
)


@dataclass
class ExperimentConfig:
    """Configuration for a domain-specific experiment."""
    domain: str
    model_id: str = "gemini-2.5-flash"
    iterations: int = 20
    difficulty: Optional[str] = None
    seed: Optional[int] = None
    system_prompt_style: str = "expert"
    output_dir: str = "./experiment_results"
    
    def __post_init__(self):
        # Validate domain
        if self.domain not in DOMAINS:
            raise ValueError(
                f"Unknown domain: {self.domain}. "
                f"Available: {list(DOMAINS.keys())}"
            )
        
        # Validate model
        if get_model_pricing(self.model_id) is None:
            raise ValueError(f"Unknown model: {self.model_id}")


@dataclass
class StageResult:
    """Result from a single pipeline stage."""
    stage_name: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    pricing_tier: str
    context_tokens: int = 0
    output_text: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class RunResult:
    """Result from a complete pipeline run."""
    run_id: str
    domain: str
    model_id: str
    prompt_template: str
    prompt_text: str
    difficulty: str
    stages: List[StageResult]
    total_cost: float
    total_latency_ms: float
    total_input_tokens: int
    total_output_tokens: int
    quality_score: Optional[float] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class DomainExperimentRunner:
    """
    Run domain-specific experiments with tiered pricing.
    
    This class integrates:
    - Domain-specific prompt templates
    - Tiered token pricing
    - Cost tracking per stage
    - Quality evaluation
    """
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.domain_config = get_domain(config.domain)
        self.cost_tracker = TieredCostTracker(config.model_id)
        self.results: List[RunResult] = []
        
    def generate_prompts(self) -> List[Dict[str, Any]]:
        """Generate prompts for this experiment."""
        return generate_experiment_prompts(
            domain=self.config.domain,
            n_prompts=self.config.iterations,
            seed=self.config.seed,
            difficulty_filter=self.config.difficulty
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this experiment."""
        style = self.config.system_prompt_style
        if style in self.domain_config.system_prompts:
            return self.domain_config.system_prompts[style]
        return self.domain_config.system_prompts.get(
            "expert", "You are a helpful assistant."
        )
    
    def simulate_llm_call(
        self,
        prompt: str,
        stage_name: str,
        context_tokens: int = 0
    ) -> StageResult:
        """
        Simulate an LLM API call with realistic token counts.
        
        In real implementation, this would call the actual API.
        This simulation generates realistic token distributions.
        """
        # Simulate input tokens (prompt length based)
        base_input = len(prompt.split()) * 1.3  # ~1.3 tokens per word
        input_tokens = int(base_input + random.gauss(50, 20))
        input_tokens = max(10, input_tokens)
        
        # Add context tokens for multi-turn stages
        total_context = input_tokens + context_tokens
        
        # Simulate output tokens based on expected length
        output_multipliers = {
            "short": (50, 150),
            "medium": (150, 400),
            "long": (400, 1000),
        }
        
        # Determine expected output based on stage
        if "generation" in stage_name or "response" in stage_name:
            min_out, max_out = output_multipliers.get("medium", (100, 300))
        elif "refinement" in stage_name:
            min_out, max_out = output_multipliers.get("long", (200, 500))
        else:
            min_out, max_out = output_multipliers.get("short", (50, 150))
        
        output_tokens = random.randint(min_out, max_out)
        
        # Calculate cost with tiered pricing
        cost_breakdown = calculate_cost_detailed(
            self.config.model_id,
            input_tokens,
            output_tokens,
            total_context
        )
        
        # Simulate latency (correlated with output tokens)
        base_latency = 500 + output_tokens * 2
        latency_ms = base_latency + random.gauss(0, 100)
        latency_ms = max(100, latency_ms)
        
        # Track this request
        self.cost_tracker.add_request(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            context_tokens=total_context,
            stage_name=stage_name
        )
        
        return StageResult(
            stage_name=stage_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost_breakdown["total_cost"],
            latency_ms=latency_ms,
            pricing_tier=cost_breakdown["pricing_tier"],
            context_tokens=total_context,
            output_text=f"[Simulated output for {stage_name}]",
            metadata={
                "input_rate": cost_breakdown["input_rate"],
                "output_rate": cost_breakdown["output_rate"],
            }
        )
    
    def run_single_prompt(
        self,
        prompt_data: Dict[str, Any],
        run_id: str
    ) -> RunResult:
        """Run a single prompt through a simulated pipeline."""
        stages = []
        accumulated_context = 0
        
        # Stage 1: Initial generation
        stage1 = self.simulate_llm_call(
            prompt=prompt_data["prompt"],
            stage_name="generation",
            context_tokens=accumulated_context
        )
        stages.append(stage1)
        accumulated_context += stage1.input_tokens + stage1.output_tokens
        
        # Stage 2: Refinement (50% chance)
        if random.random() > 0.5:
            stage2 = self.simulate_llm_call(
                prompt=f"Refine: {stage1.output_text[:100]}",
                stage_name="refinement",
                context_tokens=accumulated_context
            )
            stages.append(stage2)
            accumulated_context += stage2.input_tokens + stage2.output_tokens
        
        # Stage 3: Quality evaluation
        stage3 = self.simulate_llm_call(
            prompt="Evaluate the quality of this response",
            stage_name="evaluation",
            context_tokens=accumulated_context
        )
        stages.append(stage3)
        
        # Calculate totals
        total_cost = sum(s.cost for s in stages)
        total_latency = sum(s.latency_ms for s in stages)
        total_input = sum(s.input_tokens for s in stages)
        total_output = sum(s.output_tokens for s in stages)
        
        # Simulate quality score (correlated with model and difficulty)
        base_quality = 7.0 if "pro" in self.config.model_id.lower() else 6.5
        difficulty_modifier = {"easy": 0.5, "medium": 0, "hard": -0.5}.get(
            prompt_data.get("difficulty", "medium"), 0
        )
        quality_score = base_quality + difficulty_modifier + random.gauss(0, 0.5)
        quality_score = max(1, min(10, quality_score))
        
        return RunResult(
            run_id=run_id,
            domain=self.config.domain,
            model_id=self.config.model_id,
            prompt_template=prompt_data["template_name"],
            prompt_text=prompt_data["prompt"],
            difficulty=prompt_data.get("difficulty", "medium"),
            stages=stages,
            total_cost=total_cost,
            total_latency_ms=total_latency,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            quality_score=quality_score,
        )
    
    def run_experiment(self) -> Dict[str, Any]:
        """Run the complete experiment."""
        prompts = self.generate_prompts()
        
        print(f"\n{'='*60}")
        print(f"Running {self.config.domain.upper()} Domain Experiment")
        print(f"{'='*60}")
        print(f"Model: {self.config.model_id}")
        print(f"Iterations: {self.config.iterations}")
        print(f"Difficulty: {self.config.difficulty or 'all'}")
        print(f"{'='*60}\n")
        
        for i, prompt_data in enumerate(prompts, 1):
            run_id = f"{self.config.domain}_{i:04d}"
            result = self.run_single_prompt(prompt_data, run_id)
            self.results.append(result)
            
            if i % 5 == 0 or i == len(prompts):
                print(f"Progress: {i}/{len(prompts)} runs completed")
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate experiment report."""
        if not self.results:
            return {"error": "No results to report"}
        
        # Aggregate statistics
        total_cost = sum(r.total_cost for r in self.results)
        total_runs = len(self.results)
        avg_cost = total_cost / total_runs
        avg_quality = sum(r.quality_score for r in self.results) / total_runs
        
        # Cost by template
        template_costs = {}
        template_counts = {}
        for r in self.results:
            template_costs[r.prompt_template] = (
                template_costs.get(r.prompt_template, 0) + r.total_cost
            )
            template_counts[r.prompt_template] = (
                template_counts.get(r.prompt_template, 0) + 1
            )
        
        # Cost by stage
        stage_costs = self.cost_tracker.get_cost_by_stage()
        
        # Tier breakdown
        tracker_summary = self.cost_tracker.get_summary()
        
        report = {
            "experiment": {
                "domain": self.config.domain,
                "model_id": self.config.model_id,
                "iterations": self.config.iterations,
                "difficulty_filter": self.config.difficulty,
                "timestamp": datetime.now().isoformat(),
            },
            "summary": {
                "total_runs": total_runs,
                "total_cost": round(total_cost, 6),
                "avg_cost_per_run": round(avg_cost, 6),
                "avg_quality_score": round(avg_quality, 2),
                "total_input_tokens": tracker_summary["total_input_tokens"],
                "total_output_tokens": tracker_summary["total_output_tokens"],
            },
            "pricing_tiers": {
                "standard_requests": (
                    total_runs - tracker_summary["long_context_requests"]
                ),
                "long_context_requests": tracker_summary["long_context_requests"],
                "long_context_percentage": round(
                    tracker_summary["long_context_percentage"], 1
                ),
            },
            "cost_by_stage": {k: round(v, 6) for k, v in stage_costs.items()},
            "cost_by_template": {
                t: round(template_costs[t] / template_counts[t], 6)
                for t in template_costs
            },
            "quality_distribution": {
                "min": round(min(r.quality_score for r in self.results), 2),
                "max": round(max(r.quality_score for r in self.results), 2),
                "avg": round(avg_quality, 2),
            },
        }
        
        return report
    
    def save_results(self, output_path: Optional[str] = None):
        """Save results to JSON file."""
        if output_path is None:
            Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                f"{self.config.output_dir}/"
                f"{self.config.domain}_{timestamp}.json"
            )
        
        report = self.generate_report()
        report["detailed_results"] = [
            {
                "run_id": r.run_id,
                "template": r.prompt_template,
                "difficulty": r.difficulty,
                "total_cost": r.total_cost,
                "quality_score": r.quality_score,
                "stages": [asdict(s) for s in r.stages],
            }
            for r in self.results
        ]
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
        return output_path


def compare_models_on_domain(
    domain: str,
    models: List[str] = None,
    iterations: int = 10
) -> Dict[str, Any]:
    """
    Compare multiple models on the same domain.
    
    Args:
        domain: The domain to test
        models: List of model IDs to compare
        iterations: Number of iterations per model
    
    Returns:
        Comparison report
    """
    if models is None:
        models = ["gemini-2.5-flash", "gemini-2.5-pro"]
    
    results = {}
    
    for model in models:
        config = ExperimentConfig(
            domain=domain,
            model_id=model,
            iterations=iterations,
            seed=42  # Same seed for fair comparison
        )
        
        runner = DomainExperimentRunner(config)
        report = runner.run_experiment()
        results[model] = report["summary"]
    
    # Generate comparison
    comparison = {
        "domain": domain,
        "models_compared": models,
        "iterations_per_model": iterations,
        "results": results,
        "analysis": {
            "cost_ratio": (
                results[models[1]]["total_cost"] / 
                results[models[0]]["total_cost"]
                if len(models) > 1 else 1
            ),
            "quality_difference": (
                results[models[1]]["avg_quality_score"] - 
                results[models[0]]["avg_quality_score"]
                if len(models) > 1 else 0
            ),
        }
    }
    
    return comparison


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run domain-specific LLM cost experiments"
    )
    parser.add_argument(
        "--domain", "-d",
        choices=list(DOMAINS.keys()),
        help="Domain for the experiment"
    )
    parser.add_argument(
        "--model", "-m",
        default="gemini-2.5-flash",
        help="Model ID to use"
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=20,
        help="Number of iterations"
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default=None,
        help="Filter prompts by difficulty"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./experiment_results",
        help="Output directory"
    )
    parser.add_argument(
        "--compare-models",
        action="store_true",
        help="Compare Flash vs Pro on the domain"
    )
    parser.add_argument(
        "--list-domains",
        action="store_true",
        help="List available domains"
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List templates for a domain"
    )
    
    args = parser.parse_args()
    
    if args.list_domains:
        print("\nAvailable Domains:\n")
        for name, domain in DOMAINS.items():
            print(f"  {name}:")
            print(f"    {domain.description}")
            print(f"    Templates: {len(domain.templates)}")
            print()
        exit(0)
    
    if args.list_templates:
        if not args.domain:
            print("Error: --domain required with --list-templates")
            exit(1)
        domain = get_domain(args.domain)
        print(f"\nTemplates for '{args.domain}' domain:\n")
        for t in domain.templates:
            print(f"  {t.name}")
            print(f"    Difficulty: {t.difficulty}")
            print(f"    Expected output: {t.expected_output_length}")
            print()
        exit(0)
    
    if not args.domain:
        print("Error: --domain is required")
        parser.print_help()
        exit(1)
    
    if args.compare_models:
        print(f"\nComparing models on {args.domain} domain...")
        comparison = compare_models_on_domain(
            domain=args.domain,
            iterations=args.iterations
        )
        
        print(f"\n{'='*60}")
        print("Model Comparison Results")
        print(f"{'='*60}")
        for model, summary in comparison["results"].items():
            print(f"\n{model}:")
            print(f"  Total Cost: ${summary['total_cost']:.4f}")
            print(f"  Avg Quality: {summary['avg_quality_score']:.2f}")
        
        print(f"\nAnalysis:")
        print(f"  Cost Ratio (Pro/Flash): {comparison['analysis']['cost_ratio']:.1f}x")
        print(f"  Quality Difference: {comparison['analysis']['quality_difference']:+.2f}")
        exit(0)
    
    # Run single experiment
    config = ExperimentConfig(
        domain=args.domain,
        model_id=args.model,
        iterations=args.iterations,
        difficulty=args.difficulty,
        seed=args.seed,
        output_dir=args.output
    )
    
    runner = DomainExperimentRunner(config)
    report = runner.run_experiment()
    
    # Print summary
    print(f"\n{'='*60}")
    print("Experiment Summary")
    print(f"{'='*60}")
    print(f"Domain: {report['experiment']['domain']}")
    print(f"Model: {report['experiment']['model_id']}")
    print(f"\nCost Summary:")
    print(f"  Total Cost: ${report['summary']['total_cost']:.4f}")
    print(f"  Avg per Run: ${report['summary']['avg_cost_per_run']:.6f}")
    print(f"\nQuality:")
    print(f"  Average Score: {report['summary']['avg_quality_score']:.2f}/10")
    print(f"\nPricing Tiers:")
    print(f"  Standard: {report['pricing_tiers']['standard_requests']} requests")
    print(f"  Long Context: {report['pricing_tiers']['long_context_requests']} requests")
    print(f"\nCost by Stage:")
    for stage, cost in report['cost_by_stage'].items():
        print(f"  {stage}: ${cost:.6f}")
    
    # Save results
    runner.save_results()
