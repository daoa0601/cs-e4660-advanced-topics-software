"""
Domain Experiment Runner for LLM Cost Analysis

This module provides a unified interface for running domain-specific
LLM cost experiments with real API calls and accurate tiered pricing.

Key features:
- Domain-specific prompt generation (coding, biology, legal, etc.)
- Real Gemini API calls for accurate results
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
from ..clients import call_model


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
    Run domain-specific experiments using real API calls.
    
    This class integrates:
    - Domain-specific prompt templates
    - Real Gemini API calls
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
    
    def call_llm(
        self,
        prompt: str,
        stage_name: str,
        context_tokens: int = 0
    ) -> StageResult:
        """
        Call the Gemini API for a pipeline stage.
        """
        # Call the actual API
        response = call_model(prompt, self.config.model_id)
        
        input_tokens = response.input_tokens
        output_tokens = response.output_tokens
        
        # Add context tokens for multi-turn stages
        total_context = input_tokens + context_tokens
        
        # Calculate cost with tiered pricing
        cost_breakdown = calculate_cost_detailed(
            self.config.model_id,
            input_tokens,
            output_tokens,
            total_context
        )
        
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
            latency_ms=response.latency_ms,
            pricing_tier=cost_breakdown["pricing_tier"],
            context_tokens=total_context,
            output_text=response.text if response.success else "[API Error]",
            metadata={
                "input_rate": cost_breakdown["input_rate"],
                "output_rate": cost_breakdown["output_rate"],
                "success": response.success,
            }
        )
    
    def run_single_prompt(
        self,
        prompt_data: Dict[str, Any],
        run_id: str
    ) -> RunResult:
        """Run a single prompt through the pipeline with real API calls."""
        stages = []
        accumulated_context = 0
        
        # Stage 1: Initial generation
        stage1 = self.call_llm(
            prompt=prompt_data["prompt"],
            stage_name="generation",
            context_tokens=accumulated_context
        )
        stages.append(stage1)
        accumulated_context += stage1.input_tokens + stage1.output_tokens
        
        # Stage 2: Refinement (50% chance)
        if random.random() > 0.5:
            refinement_prompt = f"Please refine and improve this response:\n\n{stage1.output_text[:500]}\n\nProvide an improved version:"
            stage2 = self.call_llm(
                prompt=refinement_prompt,
                stage_name="refinement",
                context_tokens=accumulated_context
            )
            stages.append(stage2)
            accumulated_context += stage2.input_tokens + stage2.output_tokens
        
        # Stage 3: Quality evaluation
        eval_prompt = f"Rate the quality of this response on a scale of 1-10. Just provide the number:\n\n{stages[-1].output_text[:500]}"
        stage3 = self.call_llm(
            prompt=eval_prompt,
            stage_name="evaluation",
            context_tokens=accumulated_context
        )
        stages.append(stage3)
        
        # Calculate totals
        total_cost = sum(s.cost for s in stages)
        total_latency = sum(s.latency_ms for s in stages)
        total_input = sum(s.input_tokens for s in stages)
        total_output = sum(s.output_tokens for s in stages)
        
        # Extract quality score from evaluation response
        # Try to parse the number from the evaluation output
        quality_score = 7.0  # Default
        try:
            eval_text = stage3.output_text.strip()
            # Find first number in the response
            import re
            numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', eval_text)
            if numbers:
                quality_score = float(numbers[0])
                quality_score = max(1, min(10, quality_score))  # Clamp to 1-10
        except (ValueError, IndexError):
            pass
        
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
        Comparison report with quality-adjusted cost analysis
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
    
    # Generate comparison with quality-adjusted metrics
    flash_results = results.get(models[0], {})
    pro_results = results.get(models[1], {}) if len(models) > 1 else {}
    
    # Calculate quality-adjusted cost effectiveness
    # Cost per quality point = total_cost / avg_quality
    flash_cost_per_quality = (
        flash_results["total_cost"] / flash_results["avg_quality_score"]
        if flash_results.get("avg_quality_score", 0) > 0 else float('inf')
    )
    pro_cost_per_quality = (
        pro_results["total_cost"] / pro_results["avg_quality_score"]
        if pro_results.get("avg_quality_score", 0) > 0 else float('inf')
    )
    
    # Quality improvement percentage
    quality_improvement = (
        ((pro_results.get("avg_quality_score", 0) - flash_results.get("avg_quality_score", 0)) 
         / flash_results.get("avg_quality_score", 1)) * 100
        if flash_results.get("avg_quality_score", 0) > 0 else 0
    )
    
    # Cost increase percentage
    cost_increase = (
        ((pro_results.get("total_cost", 0) - flash_results.get("total_cost", 0)) 
         / flash_results.get("total_cost", 1)) * 100
        if flash_results.get("total_cost", 0) > 0 else 0
    )
    
    # Is Pro worth it? Compare quality gain vs cost increase
    pro_worth_it = quality_improvement > 0 and (
        quality_improvement >= cost_increase * 0.1  # Quality gain worth 10% of cost increase
        or pro_results.get("avg_quality_score", 0) >= 7.5  # Or absolute quality is high enough
    )
    
    comparison = {
        "domain": domain,
        "domain_description": get_domain(domain).description if get_domain(domain) else "",
        "models_compared": models,
        "iterations_per_model": iterations,
        "results": results,
        "analysis": {
            "cost_ratio": (
                pro_results.get("total_cost", 0) / flash_results.get("total_cost", 1)
                if flash_results.get("total_cost", 0) > 0 else 0
            ),
            "quality_difference": (
                pro_results.get("avg_quality_score", 0) - flash_results.get("avg_quality_score", 0)
            ),
            "quality_improvement_pct": round(quality_improvement, 1),
            "cost_increase_pct": round(cost_increase, 1),
            "flash_cost_per_quality_point": round(flash_cost_per_quality, 6),
            "pro_cost_per_quality_point": round(pro_cost_per_quality, 6),
            "pro_recommended": pro_worth_it,
            "recommendation": (
                "Pro RECOMMENDED: Quality improvement justifies cost premium"
                if pro_worth_it else
                "Flash RECOMMENDED: Cost savings outweigh quality difference"
            ),
        }
    }
    
    return comparison


def run_pro_advantage_analysis(iterations: int = 10) -> Dict[str, Any]:
    """
    Run a comprehensive Pro vs Flash comparison across domains.
    
    Specifically tests the complex_reasoning domain where Pro should excel.
    
    Returns:
        Analysis report showing where Pro's premium is justified
    """
    domains_to_test = ["general", "coding", "complex_reasoning"]
    
    print("\n" + "=" * 70)
    print("PRO-ADVANTAGE ANALYSIS: Finding where Gemini Pro justifies its cost")
    print("=" * 70 + "\n")
    
    all_results = {}
    
    for domain in domains_to_test:
        print(f"\n--- Testing {domain.upper()} domain ---")
        comparison = compare_models_on_domain(domain, iterations=iterations)
        all_results[domain] = comparison
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: When to use Pro vs Flash")
    print("=" * 70)
    
    for domain, result in all_results.items():
        analysis = result["analysis"]
        rec = "✓ PRO" if analysis["pro_recommended"] else "✗ Flash"
        print(f"\n{domain}:")
        print(f"  Quality Improvement: {analysis['quality_improvement_pct']:+.1f}%")
        print(f"  Cost Increase: {analysis['cost_increase_pct']:+.1f}%")
        print(f"  Recommendation: {rec}")
    
    return all_results


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
        "--pro-advantage",
        action="store_true",
        help="Run Pro-advantage analysis across domains (general, coding, complex_reasoning)"
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
    
    # Pro-advantage analysis (runs without --domain)
    if args.pro_advantage:
        results = run_pro_advantage_analysis(iterations=args.iterations)
        exit(0)
    
    if args.list_domains:
        print("\nAvailable Domains:\n")
        for name, domain in DOMAINS.items():
            pro_recommended = "(Pro-advantage)" if name == "complex_reasoning" else ""
            print(f"  {name}: {pro_recommended}")
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
        print("Error: --domain is required (or use --pro-advantage for multi-domain analysis)")
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
        
        analysis = comparison["analysis"]
        print(f"\nAnalysis:")
        print(f"  Cost Ratio (Pro/Flash): {analysis['cost_ratio']:.1f}x")
        print(f"  Quality Improvement: {analysis['quality_improvement_pct']:+.1f}%")
        print(f"  Cost per Quality (Flash): ${analysis['flash_cost_per_quality_point']:.6f}")
        print(f"  Cost per Quality (Pro): ${analysis['pro_cost_per_quality_point']:.6f}")
        print(f"\n  >>> {analysis['recommendation']}")
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
