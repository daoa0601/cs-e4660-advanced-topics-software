"""
Verifiable Problems with Ground Truth for LLM Quality Evaluation

This module provides problems with known correct answers that can be
objectively verified, enabling accurate quality comparisons between models.

Problem Types:
- Math calculations with numeric answers
- Logic puzzles with definite solutions
- Sequence/pattern recognition
- Word problems with calculable results

Each problem includes:
- prompt: The question to ask
- answer: The correct answer (for verification)
- answer_patterns: Regex patterns that match correct responses
- explanation: Why this is the correct answer
- difficulty: easy/medium/hard
- category: Type of reasoning required
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Union
import random


@dataclass
class VerifiableProblem:
    """A problem with a known correct answer."""
    id: str
    prompt: str
    answer: Union[str, int, float, bool]
    answer_patterns: List[str]  # Regex patterns that match correct answers
    category: str
    difficulty: str = "medium"
    explanation: str = ""
    
    def verify(self, response: str) -> bool:
        """Check if a response contains the correct answer."""
        response_lower = response.lower().strip()
        
        # Check each pattern
        for pattern in self.answer_patterns:
            if re.search(pattern, response_lower, re.IGNORECASE):
                return True
        
        # Also check for exact answer match
        answer_str = str(self.answer).lower()
        if answer_str in response_lower:
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "answer": self.answer,
            "category": self.category,
            "difficulty": self.difficulty,
        }


# =============================================================================
# MATH PROBLEMS
# =============================================================================

MATH_PROBLEMS = [
    # Arithmetic sequences
    VerifiableProblem(
        id="math_001",
        prompt="What is the sum of the first 100 positive integers? Show your work.",
        answer=5050,
        answer_patterns=[r"5,?050", r"5050", r"five thousand (and )?fifty"],
        category="arithmetic_series",
        difficulty="medium",
        explanation="Using formula n(n+1)/2: 100(101)/2 = 5050"
    ),
    VerifiableProblem(
        id="math_002",
        prompt="What is the sum of the first 50 odd numbers?",
        answer=2500,
        answer_patterns=[r"2,?500", r"2500", r"twenty-?five hundred"],
        category="arithmetic_series",
        difficulty="medium",
        explanation="Sum of first n odd numbers = n². 50² = 2500"
    ),
    VerifiableProblem(
        id="math_003",
        prompt="If a number is increased by 20% and then decreased by 20%, what is the net percentage change?",
        answer=-4,
        answer_patterns=[r"-4%", r"-4 ?percent", r"4% decrease", r"decrease of 4", r"net loss of 4"],
        category="percentage",
        difficulty="medium",
        explanation="1.20 × 0.80 = 0.96, which is 4% less than 1"
    ),
    
    # Compound calculations
    VerifiableProblem(
        id="math_004",
        prompt="A bacteria colony doubles every hour. If you start with 1 bacterium, how many will there be after 10 hours?",
        answer=1024,
        answer_patterns=[r"1,?024", r"1024", r"one thousand (and )?twenty-?four"],
        category="exponential_growth",
        difficulty="easy",
        explanation="2^10 = 1024"
    ),
    VerifiableProblem(
        id="math_005",
        prompt="$10,000 is invested at 10% annual compound interest. What is the value after 3 years? Round to the nearest dollar.",
        answer=13310,
        answer_patterns=[r"\$?13,?310", r"13310", r"13,310"],
        category="compound_interest",
        difficulty="medium",
        explanation="10000 × (1.10)³ = 10000 × 1.331 = $13,310"
    ),
    VerifiableProblem(
        id="math_006",
        prompt="A train travels 60 miles at 30 mph, then 60 miles at 60 mph. What is the average speed for the whole trip?",
        answer=40,
        answer_patterns=[r"40 ?mph", r"40 miles per hour", r"average speed is 40", r"answer is 40"],
        category="average_speed",
        difficulty="hard",
        explanation="Total distance = 120 miles. Time = 2 + 1 = 3 hours. Avg = 120/3 = 40 mph"
    ),
    
    # Number theory
    VerifiableProblem(
        id="math_007",
        prompt="How many prime numbers are there between 1 and 50 (inclusive)?",
        answer=15,
        answer_patterns=[r"\b15\b", r"fifteen"],
        category="number_theory",
        difficulty="medium",
        explanation="Primes: 2,3,5,7,11,13,17,19,23,29,31,37,41,43,47 = 15 primes"
    ),
    VerifiableProblem(
        id="math_008",
        prompt="What is the greatest common divisor (GCD) of 48 and 180?",
        answer=12,
        answer_patterns=[r"\b12\b", r"twelve", r"gcd is 12"],
        category="number_theory",
        difficulty="medium",
        explanation="48 = 2⁴×3, 180 = 2²×3²×5. GCD = 2²×3 = 12"
    ),
    VerifiableProblem(
        id="math_009",
        prompt="What is 7! (7 factorial)?",
        answer=5040,
        answer_patterns=[r"5,?040", r"5040"],
        category="factorial",
        difficulty="easy",
        explanation="7! = 7×6×5×4×3×2×1 = 5040"
    ),
    
    # Algebra
    VerifiableProblem(
        id="math_010",
        prompt="Solve for x: 3x + 7 = 2x + 15. What is x?",
        answer=8,
        answer_patterns=[r"x ?= ?8", r"\bx is 8\b", r"\b8\b", r"eight"],
        category="algebra",
        difficulty="easy",
        explanation="3x - 2x = 15 - 7, so x = 8"
    ),
    VerifiableProblem(
        id="math_011",
        prompt="If f(x) = 2x² - 3x + 1, what is f(3)?",
        answer=10,
        answer_patterns=[r"f\(3\) ?= ?10", r"\b10\b", r"ten", r"answer is 10"],
        category="functions",
        difficulty="easy",
        explanation="f(3) = 2(9) - 3(3) + 1 = 18 - 9 + 1 = 10"
    ),
    VerifiableProblem(
        id="math_012",
        prompt="A rectangle has a perimeter of 24 and a length that is twice its width. What is the area?",
        answer=32,
        answer_patterns=[r"area is 32", r"\b32\b square", r"\b32\b", r"thirty-?two"],
        category="geometry",
        difficulty="medium",
        explanation="2(2w + w) = 24, so w = 4, l = 8. Area = 32"
    ),
]


# =============================================================================
# LOGIC PUZZLES
# =============================================================================

LOGIC_PROBLEMS = [
    VerifiableProblem(
        id="logic_001",
        prompt="If all roses are flowers, and all flowers need water, do all roses need water? Answer yes or no.",
        answer=True,
        answer_patterns=[r"\byes\b", r"\btrue\b", r"correct", r"all roses.*need water"],
        category="syllogism",
        difficulty="easy",
        explanation="Valid syllogism: if A→B and B→C, then A→C"
    ),
    VerifiableProblem(
        id="logic_002",
        prompt="If it's raining, the ground is wet. The ground is wet. Is it definitely raining? Answer yes or no.",
        answer=False,
        answer_patterns=[r"\bno\b", r"\bfalse\b", r"not necessarily", r"cannot conclude", r"affirming the consequent"],
        category="logical_fallacy",
        difficulty="medium",
        explanation="This is affirming the consequent fallacy - the ground could be wet for other reasons"
    ),
    VerifiableProblem(
        id="logic_003",
        prompt="Alice is taller than Bob. Charlie is shorter than Bob. Who is the tallest?",
        answer="Alice",
        answer_patterns=[r"\balice\b", r"alice is (the )?tallest"],
        category="ordering",
        difficulty="easy",
        explanation="Alice > Bob > Charlie, so Alice is tallest"
    ),
    VerifiableProblem(
        id="logic_004",
        prompt="In a race, you overtake the person in 2nd place. What position are you now in?",
        answer="2nd",
        answer_patterns=[r"2nd", r"second", r"second place"],
        category="reasoning",
        difficulty="easy",
        explanation="You take their position, becoming 2nd, not 1st"
    ),
    VerifiableProblem(
        id="logic_005",
        prompt="A bat and ball cost $1.10 together. The bat costs $1 more than the ball. How much does the ball cost? Give the exact amount.",
        answer=0.05,
        answer_patterns=[r"\$?0?\.05", r"5 ?cents", r"five cents", r"\$0\.05"],
        category="algebra_word_problem",
        difficulty="hard",
        explanation="If ball = x, then bat = x + 1. x + (x + 1) = 1.10, so 2x = 0.10, x = 0.05"
    ),
    VerifiableProblem(
        id="logic_006",
        prompt="There are 3 light switches outside a room. One controls a light inside. You can only enter the room once. How do you determine which switch controls the light? (Standard answer: use heat)",
        answer="heat",
        answer_patterns=[r"\bheat\b", r"\bwarm\b", r"\bhot\b", r"touch.*bulb", r"temperature"],
        category="lateral_thinking",
        difficulty="hard",
        explanation="Turn one on for a while (heats bulb), turn it off, turn another on, enter. The hot bulb = first switch, lit = second, cold/off = third"
    ),
    VerifiableProblem(
        id="logic_007",
        prompt="How many months have 28 days?",
        answer=12,
        answer_patterns=[r"\b12\b", r"\btwelve\b", r"all.*months"],
        category="trick_question",
        difficulty="easy",
        explanation="All 12 months have at least 28 days"
    ),
    VerifiableProblem(
        id="logic_008",
        prompt="A farmer has 17 sheep. All but 9 run away. How many sheep does the farmer have left?",
        answer=9,
        answer_patterns=[r"\b9\b", r"\bnine\b"],
        category="word_problem",
        difficulty="easy",
        explanation="'All but 9' means 9 remain"
    ),
]


# =============================================================================
# SEQUENCE PROBLEMS
# =============================================================================

SEQUENCE_PROBLEMS = [
    VerifiableProblem(
        id="seq_001",
        prompt="What is the next number in the sequence: 2, 4, 8, 16, 32, ?",
        answer=64,
        answer_patterns=[r"\b64\b", r"sixty-?four"],
        category="geometric_sequence",
        difficulty="easy",
        explanation="Each number doubles: 32 × 2 = 64"
    ),
    VerifiableProblem(
        id="seq_002",
        prompt="What is the next number in the Fibonacci sequence: 1, 1, 2, 3, 5, 8, 13, ?",
        answer=21,
        answer_patterns=[r"\b21\b", r"twenty-?one"],
        category="fibonacci",
        difficulty="easy",
        explanation="8 + 13 = 21"
    ),
    VerifiableProblem(
        id="seq_003",
        prompt="What is the next number: 1, 4, 9, 16, 25, ?",
        answer=36,
        answer_patterns=[r"\b36\b", r"thirty-?six"],
        category="square_numbers",
        difficulty="easy",
        explanation="These are squares: 6² = 36"
    ),
    VerifiableProblem(
        id="seq_004",
        prompt="What comes next: 1, 8, 27, 64, 125, ?",
        answer=216,
        answer_patterns=[r"\b216\b", r"two hundred (and )?sixteen"],
        category="cube_numbers",
        difficulty="medium",
        explanation="These are cubes: 6³ = 216"
    ),
    VerifiableProblem(
        id="seq_005",
        prompt="What is the next prime number after 97?",
        answer=101,
        answer_patterns=[r"\b101\b", r"one hundred (and )?one"],
        category="prime_numbers",
        difficulty="medium",
        explanation="97, 98(no), 99(no), 100(no), 101 is prime"
    ),
]


# =============================================================================
# WORD PROBLEMS WITH CALCULATIONS
# =============================================================================

WORD_PROBLEMS = [
    VerifiableProblem(
        id="word_001",
        prompt="A store offers 25% off, then an additional 10% off the sale price. What is the total percentage discount?",
        answer=32.5,
        answer_patterns=[r"32\.5", r"32\.5%", r"32\.5 ?percent"],
        category="percentage",
        difficulty="medium",
        explanation="0.75 × 0.90 = 0.675, which is 32.5% off"
    ),
    VerifiableProblem(
        id="word_002",
        prompt="If 5 machines take 5 minutes to make 5 widgets, how many minutes would 100 machines take to make 100 widgets?",
        answer=5,
        answer_patterns=[r"\b5\b minutes", r"\bfive\b minutes", r"answer is 5", r"still 5"],
        category="rate_problem",
        difficulty="hard",
        explanation="Each machine makes 1 widget in 5 minutes. 100 machines make 100 widgets in 5 minutes."
    ),
    VerifiableProblem(
        id="word_003",
        prompt="A snail climbs 3 feet up a wall during the day but slides down 2 feet at night. Starting from the ground, how many days to reach the top of a 10-foot wall?",
        answer=8,
        answer_patterns=[r"\b8\b days", r"\beight\b days", r"answer is 8", r"on day 8"],
        category="reasoning",
        difficulty="hard",
        explanation="After 7 days: 7 feet. On day 8, climbs 3 to reach 10 feet (before sliding)."
    ),
    VerifiableProblem(
        id="word_004",
        prompt="A lily pad doubles in size every day. If it takes 48 days for the pad to cover the entire lake, how many days does it take to cover half the lake?",
        answer=47,
        answer_patterns=[r"\b47\b", r"forty-?seven", r"day 47"],
        category="exponential",
        difficulty="medium",
        explanation="If it doubles to full coverage on day 48, it was half on day 47"
    ),
    VerifiableProblem(
        id="word_005",
        prompt="You have 12 coins, one is fake and lighter. Using a balance scale, what is the minimum number of weighings needed to find the fake coin?",
        answer=3,
        answer_patterns=[r"\b3\b", r"\bthree\b", r"three weighings"],
        category="optimization",
        difficulty="hard",
        explanation="Divide into 3 groups: 4-4-4. Weigh two groups, identify lighter group, repeat."
    ),
]


# =============================================================================
# ALL PROBLEMS COMBINED
# =============================================================================

ALL_VERIFIABLE_PROBLEMS: List[VerifiableProblem] = (
    MATH_PROBLEMS + LOGIC_PROBLEMS + SEQUENCE_PROBLEMS + WORD_PROBLEMS
)


def get_problems_by_category(category: str) -> List[VerifiableProblem]:
    """Get all problems of a specific category."""
    return [p for p in ALL_VERIFIABLE_PROBLEMS if p.category == category]


def get_problems_by_difficulty(difficulty: str) -> List[VerifiableProblem]:
    """Get all problems of a specific difficulty."""
    return [p for p in ALL_VERIFIABLE_PROBLEMS if p.difficulty == difficulty]


def sample_problems(
    n: int,
    difficulty: Optional[str] = None,
    categories: Optional[List[str]] = None,
    seed: Optional[int] = None
) -> List[VerifiableProblem]:
    """
    Sample n problems, optionally filtered by difficulty or category.
    """
    if seed is not None:
        random.seed(seed)
    
    problems = ALL_VERIFIABLE_PROBLEMS.copy()
    
    if difficulty:
        problems = [p for p in problems if p.difficulty == difficulty]
    
    if categories:
        problems = [p for p in problems if p.category in categories]
    
    if len(problems) < n:
        # Sample with replacement if not enough
        return random.choices(problems, k=n)
    
    return random.sample(problems, n)


def verify_response(problem_id: str, response: str) -> Dict[str, Any]:
    """
    Verify a response against a problem's ground truth.
    
    Returns dict with:
        - correct: bool
        - expected: the correct answer
        - explanation: why this is correct
    """
    problem = next((p for p in ALL_VERIFIABLE_PROBLEMS if p.id == problem_id), None)
    if problem is None:
        return {"correct": False, "error": f"Unknown problem: {problem_id}"}
    
    is_correct = problem.verify(response)
    
    return {
        "correct": is_correct,
        "expected": problem.answer,
        "explanation": problem.explanation,
        "problem_id": problem_id,
        "category": problem.category,
        "difficulty": problem.difficulty,
    }


def list_categories() -> List[str]:
    """List all unique categories."""
    return list(set(p.category for p in ALL_VERIFIABLE_PROBLEMS))


def list_statistics() -> Dict[str, Any]:
    """Get statistics about available problems."""
    by_difficulty = {}
    by_category = {}
    
    for p in ALL_VERIFIABLE_PROBLEMS:
        by_difficulty[p.difficulty] = by_difficulty.get(p.difficulty, 0) + 1
        by_category[p.category] = by_category.get(p.category, 0) + 1
    
    return {
        "total_problems": len(ALL_VERIFIABLE_PROBLEMS),
        "by_difficulty": by_difficulty,
        "by_category": by_category,
    }


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verifiable problems for LLM testing")
    parser.add_argument("--list", action="store_true", help="List all problems")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--test", type=str, help="Test a specific problem ID")
    parser.add_argument("--response", type=str, help="Response to verify")
    
    args = parser.parse_args()
    
    if args.stats:
        stats = list_statistics()
        print("\nVerifiable Problems Statistics:")
        print(f"  Total: {stats['total_problems']}")
        print(f"\n  By Difficulty:")
        for d, c in stats['by_difficulty'].items():
            print(f"    {d}: {c}")
        print(f"\n  By Category:")
        for cat, c in sorted(stats['by_category'].items()):
            print(f"    {cat}: {c}")
    
    elif args.list:
        print("\nAll Verifiable Problems:\n")
        for p in ALL_VERIFIABLE_PROBLEMS:
            print(f"  [{p.id}] ({p.difficulty}) {p.category}")
            print(f"    Q: {p.prompt[:60]}...")
            print(f"    A: {p.answer}")
            print()
    
    elif args.test and args.response:
        result = verify_response(args.test, args.response)
        print(f"\nVerification Result:")
        print(f"  Correct: {result['correct']}")
        print(f"  Expected: {result.get('expected')}")
        print(f"  Explanation: {result.get('explanation')}")
