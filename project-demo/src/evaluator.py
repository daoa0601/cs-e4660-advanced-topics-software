"""
Quality evaluation for LLM outputs.

Provides multiple quality metrics to analyze the cost-quality tradeoff.
"""

import re
from dataclasses import dataclass
from typing import Optional

from .clients import call_model
from .cost_calculator import calculate_cost


@dataclass
class QualityScore:
    """Quality score for a pipeline output."""
    # Automated metrics (no LLM call needed)
    response_length: int
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    
    # Structure metrics
    has_structure: bool  # Has bullet points, numbered lists, or clear sections
    vocabulary_richness: float  # Unique words / total words
    
    # LLM-evaluated metrics (optional, costs extra)
    relevance_score: Optional[float] = None  # 0-10
    completeness_score: Optional[float] = None  # 0-10
    clarity_score: Optional[float] = None  # 0-10
    llm_evaluation_cost: float = 0.0
    
    @property
    def automated_score(self) -> float:
        """Composite score from automated metrics (0-100)."""
        score = 0
        
        # Length score (0-30): Penalize very short or excessively long
        if 100 <= self.response_length <= 2000:
            score += 30
        elif 50 <= self.response_length < 100 or 2000 < self.response_length <= 4000:
            score += 15
        else:
            score += 5
        
        # Structure bonus (0-20)
        if self.has_structure:
            score += 20
        
        # Vocabulary richness (0-25)
        score += min(25, self.vocabulary_richness * 50)
        
        # Sentence quality (0-25): Prefer medium-length sentences
        if 10 <= self.avg_sentence_length <= 25:
            score += 25
        elif 5 <= self.avg_sentence_length < 10 or 25 < self.avg_sentence_length <= 40:
            score += 15
        else:
            score += 5
        
        return round(score, 2)
    
    @property
    def llm_score(self) -> Optional[float]:
        """Average of LLM-evaluated scores (0-10), if available."""
        scores = [s for s in [self.relevance_score, self.completeness_score, self.clarity_score] if s is not None]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)
    
    @property
    def combined_score(self) -> float:
        """Combined score: automated (40%) + LLM (60%) if available, else automated only."""
        if self.llm_score is not None:
            return round(self.automated_score * 0.4 + self.llm_score * 10 * 0.6, 2)
        return self.automated_score


def count_sentences(text: str) -> int:
    """Count sentences in text."""
    # Simple sentence detection
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def has_structure(text: str) -> bool:
    """Check if text has structural elements."""
    patterns = [
        r'^\s*[-•*]\s+',  # Bullet points
        r'^\s*\d+[.)]\s+',  # Numbered lists
        r'^#+\s+',  # Markdown headers
        r'\n\n',  # Paragraph breaks
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True
    return False


def vocabulary_richness(text: str) -> float:
    """Calculate vocabulary richness (unique words / total words)."""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    unique_words = set(words)
    return len(unique_words) / len(words)


def evaluate_automated(text: str) -> QualityScore:
    """
    Evaluate text quality using automated metrics only (no LLM calls).
    
    Args:
        text: The text to evaluate
    
    Returns:
        QualityScore with automated metrics filled in
    """
    words = re.findall(r'\b\w+\b', text)
    sentences = count_sentences(text)
    
    return QualityScore(
        response_length=len(text),
        word_count=len(words),
        sentence_count=sentences,
        avg_sentence_length=len(words) / max(sentences, 1),
        has_structure=has_structure(text),
        vocabulary_richness=vocabulary_richness(text),
    )


def evaluate_with_llm(
    text: str, 
    original_query: str, 
    model: str = "flash"
) -> QualityScore:
    """
    Evaluate text quality using both automated metrics and LLM evaluation.
    
    This costs extra API calls but provides more meaningful quality scores.
    
    Args:
        text: The text to evaluate
        original_query: The original question/task
        model: Model to use for evaluation (default: flash for cost efficiency)
    
    Returns:
        QualityScore with all metrics filled in
    """
    # Get automated metrics first
    score = evaluate_automated(text)
    
    # LLM evaluation prompt
    eval_prompt = f"""Evaluate the following response on three criteria. 
For each, provide a score from 0-10 where 10 is best.

Original question/task:
{original_query}

Response to evaluate:
{text}

Provide your evaluation in exactly this format:
RELEVANCE: [score]
COMPLETENESS: [score]
CLARITY: [score]

Only output the three scores in the format above, nothing else."""

    response = call_model(eval_prompt, model)
    
    if response.success:
        # Parse scores from response
        try:
            relevance_match = re.search(r'RELEVANCE:\s*(\d+(?:\.\d+)?)', response.text)
            completeness_match = re.search(r'COMPLETENESS:\s*(\d+(?:\.\d+)?)', response.text)
            clarity_match = re.search(r'CLARITY:\s*(\d+(?:\.\d+)?)', response.text)
            
            if relevance_match:
                score.relevance_score = min(10, float(relevance_match.group(1)))
            if completeness_match:
                score.completeness_score = min(10, float(completeness_match.group(1)))
            if clarity_match:
                score.clarity_score = min(10, float(clarity_match.group(1)))
        except (ValueError, AttributeError):
            pass  # Keep None values if parsing fails
        
        # Track evaluation cost
        score.llm_evaluation_cost = calculate_cost(
            response.input_tokens,
            response.output_tokens,
            model
        )
    
    return score


def evaluate_cost_quality_ratio(cost: float, quality_score: float) -> float:
    """
    Calculate cost-quality ratio (lower is better).
    
    Args:
        cost: Total cost in USD
        quality_score: Quality score (0-100)
    
    Returns:
        Cost per quality point (in millicents)
    """
    if quality_score == 0:
        return float('inf')
    # Return cost in millicents per quality point
    return (cost * 100000) / quality_score


@dataclass
class CostQualityAnalysis:
    """Analysis of cost-quality tradeoff."""
    pipeline_name: str
    model: str
    total_cost: float
    quality_score: float
    cost_per_quality_point: float
    evaluation_cost: float
    
    @property
    def effective_cost(self) -> float:
        """Total cost including evaluation."""
        return self.total_cost + self.evaluation_cost


def analyze_cost_quality(
    pipeline_name: str,
    model: str,
    total_cost: float,
    output_text: str,
    original_query: str,
    use_llm_eval: bool = False,
) -> CostQualityAnalysis:
    """
    Perform complete cost-quality analysis.
    
    Args:
        pipeline_name: Name of the pipeline
        model: Model used
        total_cost: Total pipeline cost
        output_text: Final output text
        original_query: Original input query
        use_llm_eval: Whether to use LLM for quality evaluation
    
    Returns:
        CostQualityAnalysis with all metrics
    """
    if use_llm_eval:
        quality = evaluate_with_llm(output_text, original_query)
    else:
        quality = evaluate_automated(output_text)
    
    return CostQualityAnalysis(
        pipeline_name=pipeline_name,
        model=model,
        total_cost=total_cost,
        quality_score=quality.combined_score,
        cost_per_quality_point=evaluate_cost_quality_ratio(total_cost, quality.combined_score),
        evaluation_cost=quality.llm_evaluation_cost,
    )
