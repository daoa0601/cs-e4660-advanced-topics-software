"""
Verified Experiment Runner for LLM Quality Comparison

This module runs experiments using verifiable problems with ground truth,
enabling objective quality measurement between models.

Unlike the domain experiment runner which uses simulated quality scores,
this module uses actual LLM responses verified against known correct answers.

Usage:
    python -m src.experiments.verified_experiment --iterations 20
    python -m src.experiments.verified_experiment --compare-models
    python -m src.experiments.verified_experiment --difficulty hard
    python -m src.experiments.verified_experiment --live  # Use real API calls
"""

import json
import random
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path

from ..config.verifiable_problems import (
    VerifiableProblem,
    ALL_VERIFIABLE_PROBLEMS,
    sample_problems,
    verify_response,
    list_statistics,
)
from ..pricing.tiered_pricing import (
    calculate_cost_detailed,
    TieredCostTracker,
    get_model_pricing,
)
from ..vertex_client import call_model


@dataclass
class VerifiedResult:
    """Result from a single verified experiment run."""
    problem_id: str
    problem_category: str
    problem_difficulty: str
    prompt: str
    expected_answer: Any
    model_response: str
    is_correct: bool
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    model_id: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass 
class VerifiedExperimentConfig:
    """Configuration for verified experiment."""
    model_id: str = "gemini-2.5-flash"
    iterations: int = 20
    difficulty: Optional[str] = None  # easy, medium, hard, or None for all
    categories: Optional[List[str]] = None
    seed: Optional[int] = None
    output_dir: str = "./experiment_results"
    
    def __post_init__(self):
        if get_model_pricing(self.model_id) is None:
            raise ValueError(f"Unknown model: {self.model_id}")


class VerifiedExperimentRunner:
    """
    Run experiments with verifiable ground truth using real API calls.
    
    This runner:
    1. Samples problems from the verifiable problem set
    2. Calls the Gemini API for each problem
    3. Verifies responses against known answers
    4. Reports actual accuracy with real costs
    """
    
    def __init__(self, config: VerifiedExperimentConfig):
        self.config = config
        self.cost_tracker = TieredCostTracker(config.model_id)
        self.results: List[VerifiedResult] = []
    
    def get_problems(self) -> List[VerifiableProblem]:
        """Get problems for this experiment."""
        return sample_problems(
            n=self.config.iterations,
            difficulty=self.config.difficulty,
            categories=self.config.categories,
            seed=self.config.seed
        )
    
    def call_llm(self, problem: VerifiableProblem) -> Dict[str, Any]:
        """
        Call the Gemini API for a problem.
        """
        # Create a clear prompt for the problem
        prompt = f"""{problem.prompt}

Provide your answer clearly. If this is a math problem, show your work and state the final numerical answer.
If this is a factual question, provide the answer directly.

Answer:"""
        
        # Call the model
        response = call_model(prompt, self.config.model_id)
        
        if not response.success:
            return {
                "response": f"[API Error: {response.error_message}]",
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_ms": 0,
            }
        
        return {
            "response": response.text,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "latency_ms": response.latency_ms,
        }
    
    def run_single_problem(self, problem: VerifiableProblem) -> VerifiedResult:
        """Run a single problem and verify the result."""
        # Get LLM response via real API call
        llm_result = self.call_llm(problem)
        
        # Verify the response
        is_correct = problem.verify(llm_result["response"])
        
        # Calculate cost
        cost_breakdown = calculate_cost_detailed(
            self.config.model_id,
            llm_result["input_tokens"],
            llm_result["output_tokens"],
            0  # No context accumulation for single-turn
        )
        
        # Track costs
        self.cost_tracker.add_request(
            input_tokens=llm_result["input_tokens"],
            output_tokens=llm_result["output_tokens"],
            stage_name=problem.category
        )
        
        return VerifiedResult(
            problem_id=problem.id,
            problem_category=problem.category,
            problem_difficulty=problem.difficulty,
            prompt=problem.prompt,
            expected_answer=problem.answer,
            model_response=llm_result["response"],
            is_correct=is_correct,
            input_tokens=llm_result["input_tokens"],
            output_tokens=llm_result["output_tokens"],
            cost=cost_breakdown["total_cost"],
            latency_ms=llm_result["latency_ms"],
            model_id=self.config.model_id,
        )
    
    def run_experiment(self) -> Dict[str, Any]:
        """Run the complete experiment."""
        problems = self.get_problems()
        
        print(f"\n{'='*60}")
        print(f"VERIFIED EXPERIMENT: {self.config.model_id}")
        print(f"{'='*60}")
        print(f"Problems: {len(problems)}")
        print(f"Difficulty: {self.config.difficulty or 'all'}")
        print(f"{'='*60}\n")
        
        for i, problem in enumerate(problems, 1):
            result = self.run_single_problem(problem)
            self.results.append(result)
            
            if i % 5 == 0 or i == len(problems):
                correct = sum(1 for r in self.results if r.is_correct)
                print(f"Progress: {i}/{len(problems)} | Accuracy: {correct}/{i} ({100*correct/i:.1f}%)")
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate experiment report with accuracy metrics."""
        if not self.results:
            return {"error": "No results"}
        
        # Overall accuracy
        correct = sum(1 for r in self.results if r.is_correct)
        total = len(self.results)
        accuracy = correct / total
        
        # Accuracy by difficulty
        by_difficulty = {}
        for diff in ["easy", "medium", "hard"]:
            diff_results = [r for r in self.results if r.problem_difficulty == diff]
            if diff_results:
                diff_correct = sum(1 for r in diff_results if r.is_correct)
                by_difficulty[diff] = {
                    "total": len(diff_results),
                    "correct": diff_correct,
                    "accuracy": round(diff_correct / len(diff_results), 3),
                }
        
        # Accuracy by category
        by_category = {}
        for r in self.results:
            cat = r.problem_category
            if cat not in by_category:
                by_category[cat] = {"total": 0, "correct": 0}
            by_category[cat]["total"] += 1
            if r.is_correct:
                by_category[cat]["correct"] += 1
        
        for cat in by_category:
            by_category[cat]["accuracy"] = round(
                by_category[cat]["correct"] / by_category[cat]["total"], 3
            )
        
        # Cost summary
        tracker_summary = self.cost_tracker.get_summary()
        total_cost = sum(r.cost for r in self.results)
        
        report = {
            "experiment": {
                "model_id": self.config.model_id,
                "total_problems": total,
                "difficulty_filter": self.config.difficulty,
                "timestamp": datetime.now().isoformat(),
            },
            "accuracy": {
                "overall": round(accuracy, 3),
                "correct": correct,
                "total": total,
                "by_difficulty": by_difficulty,
                "by_category": by_category,
            },
            "cost": {
                "total": round(total_cost, 6),
                "per_problem": round(total_cost / total, 6),
                "per_correct_answer": round(total_cost / max(1, correct), 6),
                "total_input_tokens": tracker_summary["total_input_tokens"],
                "total_output_tokens": tracker_summary["total_output_tokens"],
            },
        }
        
        return report
    
    def save_results(self, output_path: Optional[str] = None):
        """Save results to JSON file."""
        if output_path is None:
            Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"{self.config.output_dir}/verified_{self.config.model_id}_{timestamp}.json"
        
        report = self.generate_report()
        report["detailed_results"] = [asdict(r) for r in self.results]
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        return output_path


def compare_models_verified(
    models: List[str] = None,
    iterations: int = 20,
    difficulty: Optional[str] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Compare models on verifiable problems with ground truth.
    
    This gives objective accuracy comparison, not simulated quality.
    """
    if models is None:
        models = ["gemini-2.5-flash", "gemini-2.5-pro"]
    
    results = {}
    
    for model in models:
        config = VerifiedExperimentConfig(
            model_id=model,
            iterations=iterations,
            difficulty=difficulty,
            seed=seed  # Same problems for fair comparison
        )
        
        runner = VerifiedExperimentRunner(config)
        report = runner.run_experiment()
        results[model] = report
    
    # Generate comparison
    flash_report = results.get(models[0], {})
    pro_report = results.get(models[1], {}) if len(models) > 1 else {}
    
    flash_acc = flash_report.get("accuracy", {}).get("overall", 0)
    pro_acc = pro_report.get("accuracy", {}).get("overall", 0)
    flash_cost = flash_report.get("cost", {}).get("total", 0)
    pro_cost = pro_report.get("cost", {}).get("total", 0)
    
    # Accuracy improvement
    acc_improvement = ((pro_acc - flash_acc) / max(0.001, flash_acc)) * 100
    
    # Cost increase
    cost_increase = ((pro_cost - flash_cost) / max(0.0001, flash_cost)) * 100
    
    # Cost per correct answer
    flash_correct = flash_report.get("accuracy", {}).get("correct", 1)
    pro_correct = pro_report.get("accuracy", {}).get("correct", 1)
    flash_cost_per_correct = flash_cost / max(1, flash_correct)
    pro_cost_per_correct = pro_cost / max(1, pro_correct)
    
    comparison = {
        "models": models,
        "iterations": iterations,
        "difficulty": difficulty,
        "results": {
            models[0]: {
                "accuracy": flash_acc,
                "correct": flash_correct,
                "total_cost": round(flash_cost, 6),
                "cost_per_correct": round(flash_cost_per_correct, 6),
            },
            models[1]: {
                "accuracy": pro_acc,
                "correct": pro_correct,
                "total_cost": round(pro_cost, 6),
                "cost_per_correct": round(pro_cost_per_correct, 6),
            } if len(models) > 1 else {},
        },
        "analysis": {
            "accuracy_improvement_pct": round(acc_improvement, 1),
            "cost_increase_pct": round(cost_increase, 1),
            "flash_cost_per_correct": round(flash_cost_per_correct, 6),
            "pro_cost_per_correct": round(pro_cost_per_correct, 6),
            "pro_recommended": pro_acc > flash_acc and (
                acc_improvement >= cost_increase * 0.1 or pro_acc >= 0.8
            ),
        },
    }
    
    return comparison


def run_verified_comparison_report(iterations: int = 20, seed: int = 42):
    """
    Run a full verified comparison and print results.
    """
    print("\n" + "=" * 70)
    print("VERIFIED MODEL COMPARISON: Flash vs Pro with Ground Truth")
    print("=" * 70)
    
    # Compare on all difficulties
    all_comparison = compare_models_verified(iterations=iterations, seed=seed)
    
    # Compare on hard problems only
    hard_comparison = compare_models_verified(
        iterations=iterations, 
        difficulty="hard", 
        seed=seed
    )
    
    print("\n" + "=" * 70)
    print("RESULTS: All Difficulties")
    print("=" * 70)
    for model, data in all_comparison["results"].items():
        if data:
            print(f"\n{model}:")
            print(f"  Accuracy: {data['accuracy']:.1%} ({data['correct']}/{iterations})")
            print(f"  Total Cost: ${data['total_cost']:.4f}")
            print(f"  Cost per Correct: ${data['cost_per_correct']:.6f}")
    
    analysis = all_comparison["analysis"]
    print(f"\nAnalysis (All):")
    print(f"  Accuracy Improvement: {analysis['accuracy_improvement_pct']:+.1f}%")
    print(f"  Cost Increase: {analysis['cost_increase_pct']:+.1f}%")
    
    print("\n" + "=" * 70)
    print("RESULTS: Hard Problems Only")
    print("=" * 70)
    for model, data in hard_comparison["results"].items():
        if data:
            print(f"\n{model}:")
            print(f"  Accuracy: {data['accuracy']:.1%} ({data['correct']}/{iterations})")
    
    hard_analysis = hard_comparison["analysis"]
    print(f"\nAnalysis (Hard):")
    print(f"  Accuracy Improvement: {hard_analysis['accuracy_improvement_pct']:+.1f}%")
    
    print("\n" + "=" * 70)
    recommendation = (
        "✓ PRO RECOMMENDED for hard reasoning tasks"
        if hard_analysis["accuracy_improvement_pct"] > 30
        else "Flash may be sufficient for most tasks"
    )
    print(f"RECOMMENDATION: {recommendation}")
    print("=" * 70)
    
    return {"all": all_comparison, "hard": hard_comparison}


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run verified experiments with ground truth"
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
        help="Number of problems"
    )
    parser.add_argument(
        "--difficulty", "-d",
        choices=["easy", "medium", "hard"],
        default=None,
        help="Filter by difficulty"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed"
    )
    parser.add_argument(
        "--compare-models",
        action="store_true",
        help="Compare Flash vs Pro"
    )
    parser.add_argument(
        "--full-report",
        action="store_true",
        help="Run full comparison report"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./experiment_results",
        help="Output directory"
    )
    
    args = parser.parse_args()
    
    if args.full_report:
        run_verified_comparison_report(iterations=args.iterations, seed=args.seed)
        exit(0)
    
    if args.compare_models:
        comparison = compare_models_verified(
            iterations=args.iterations,
            difficulty=args.difficulty,
            seed=args.seed
        )
        
        print("\n" + "=" * 60)
        print("Model Comparison (Verified)")
        print("=" * 60)
        
        for model, data in comparison["results"].items():
            if data:
                print(f"\n{model}:")
                print(f"  Accuracy: {data['accuracy']:.1%}")
                print(f"  Correct: {data['correct']}/{args.iterations}")
                print(f"  Total Cost: ${data['total_cost']:.4f}")
                print(f"  Cost/Correct: ${data['cost_per_correct']:.6f}")
        
        print(f"\nAnalysis:")
        print(f"  Accuracy Boost: {comparison['analysis']['accuracy_improvement_pct']:+.1f}%")
        print(f"  Cost Increase: {comparison['analysis']['cost_increase_pct']:+.1f}%")
        rec = "PRO" if comparison["analysis"]["pro_recommended"] else "FLASH"
        print(f"\n  >>> Recommendation: {rec}")
        exit(0)
    
    # Single model experiment
    config = VerifiedExperimentConfig(
        model_id=args.model,
        iterations=args.iterations,
        difficulty=args.difficulty,
        seed=args.seed,
        output_dir=args.output,
    )
    
    print(f"\n🔴 Running verified experiment with {args.model} (real API calls)")
    
    runner = VerifiedExperimentRunner(config)
    report = runner.run_experiment()
    
    print(f"\n{'='*60}")
    print("Experiment Summary")
    print(f"{'='*60}")
    print(f"Model: {report['experiment']['model_id']}")
    print(f"\nAccuracy:")
    print(f"  Overall: {report['accuracy']['overall']:.1%}")
    print(f"  Correct: {report['accuracy']['correct']}/{report['accuracy']['total']}")
    if report['accuracy']['by_difficulty']:
        print(f"\n  By Difficulty:")
        for diff, data in report['accuracy']['by_difficulty'].items():
            print(f"    {diff}: {data['accuracy']:.1%} ({data['correct']}/{data['total']})")
    print(f"\nCost:")
    print(f"  Total: ${report['cost']['total']:.4f}")
    print(f"  Per Correct: ${report['cost']['per_correct_answer']:.6f}")
    
    runner.save_results()
