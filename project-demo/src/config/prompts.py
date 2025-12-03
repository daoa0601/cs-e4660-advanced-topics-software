"""
Prompt templates with A/B testing support.

Each prompt template can have multiple variants for testing different
prompt engineering strategies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import random


class PromptVariant(Enum):
    """Standard variant types for A/B testing."""
    CONTROL = "control"           # Baseline prompt
    CONCISE = "concise"           # Shorter, more direct
    DETAILED = "detailed"         # More explicit instructions
    STRUCTURED = "structured"     # With explicit output format
    COT = "cot"                   # Chain-of-thought style
    FEW_SHOT = "few_shot"         # With examples
    PERSONA = "persona"           # With role/persona


@dataclass
class PromptTemplate:
    """
    A prompt template with multiple variants for A/B testing.
    
    Usage:
        template = PromptTemplate(
            name="summarize",
            variants={
                "control": "Summarize: {text}",
                "detailed": "Read the following text carefully and provide a comprehensive summary: {text}",
                "structured": "Summarize the text below. Format: 1) Main point 2) Key details 3) Conclusion\n\n{text}",
            }
        )
        
        # Use specific variant
        prompt = template.render(variant="detailed", text="...")
        
        # Random variant for A/B testing
        prompt, variant_used = template.render_random(text="...")
    """
    name: str
    variants: Dict[str, str]
    default_variant: str = "control"
    description: str = ""
    
    def render(self, variant: Optional[str] = None, **kwargs) -> str:
        """
        Render the prompt template with given variant and variables.
        
        Args:
            variant: Which variant to use (default: control)
            **kwargs: Variables to substitute in the template
        
        Returns:
            Rendered prompt string
        """
        variant = variant or self.default_variant
        if variant not in self.variants:
            raise ValueError(f"Unknown variant '{variant}' for prompt '{self.name}'. "
                           f"Available: {list(self.variants.keys())}")
        
        template = self.variants[variant]
        return template.format(**kwargs)
    
    def render_random(self, **kwargs) -> tuple[str, str]:
        """
        Render with a randomly selected variant (for A/B testing).
        
        Returns:
            Tuple of (rendered_prompt, variant_name)
        """
        variant = random.choice(list(self.variants.keys()))
        return self.render(variant=variant, **kwargs), variant
    
    def list_variants(self) -> List[str]:
        """List all available variants."""
        return list(self.variants.keys())


# =============================================================================
# Standard Prompt Templates
# =============================================================================

GENERATION_PROMPTS = PromptTemplate(
    name="generation",
    description="Basic text generation prompts",
    variants={
        "control": "{query}",
        "concise": "Answer briefly and directly: {query}",
        "detailed": """Please provide a thorough and comprehensive answer to the following question. 
Include relevant details, examples, and explanations where appropriate.

Question: {query}

Answer:""",
        "structured": """Answer the following question with a clear structure:
1. Brief summary (1-2 sentences)
2. Main explanation
3. Key takeaways

Question: {query}""",
        "cot": """Think through this step by step before providing your answer.

Question: {query}

Let me think about this carefully:""",
        "persona": """You are an expert assistant known for clear, accurate, and helpful responses.

Question: {query}

Expert response:""",
    }
)

CRITIQUE_PROMPTS = PromptTemplate(
    name="critique",
    description="Prompts for critiquing/reviewing content",
    variants={
        "control": """Review this response and identify areas for improvement:

{response}

Critique:""",
        "concise": "List 3 specific improvements for: {response}",
        "detailed": """Carefully analyze the following response for:
1. Accuracy - Are there any factual errors?
2. Completeness - What important information is missing?
3. Clarity - What could be explained better?
4. Structure - How could the organization be improved?

Response to analyze:
{response}

Detailed critique:""",
        "structured": """Review the response below and provide feedback in this format:
- STRENGTHS: [list strengths]
- WEAKNESSES: [list weaknesses]  
- SUGGESTIONS: [specific improvements]

Response:
{response}""",
        "socratic": """Consider this response critically. Ask yourself:
- What assumptions does it make?
- What evidence supports the claims?
- What alternative perspectives exist?

Response:
{response}

Critical analysis:""",
    }
)

REFINEMENT_PROMPTS = PromptTemplate(
    name="refinement",
    description="Prompts for refining/improving content",
    variants={
        "control": """Improve this response based on the feedback:

Original: {original}
Feedback: {feedback}

Improved response:""",
        "concise": "Rewrite more clearly, addressing: {feedback}\n\nOriginal: {original}",
        "detailed": """You are refining a response based on specific feedback. 

Original response:
{original}

Feedback received:
{feedback}

Instructions:
1. Address each point in the feedback
2. Maintain the accurate parts of the original
3. Improve clarity and structure
4. Ensure completeness

Refined response:""",
        "iterative": """This is iteration {iteration} of refinement.

Previous version:
{original}

Issues to fix:
{feedback}

Make targeted improvements while preserving what works well:""",
    }
)

EXTRACTION_PROMPTS = PromptTemplate(
    name="extraction",
    description="Prompts for extracting information from text",
    variants={
        "control": "Extract the key information from:\n\n{text}",
        "concise": "Key points from: {text}",
        "detailed": """Analyze the following text and extract:
1. Main topics and themes
2. Key facts and figures
3. Important entities (people, organizations, places)
4. Relationships between concepts

Text:
{text}

Extracted information:""",
        "structured": """Extract information from the text in JSON-like format:
- TOPICS: []
- KEY_FACTS: []
- ENTITIES: []
- SUMMARY: ""

Text:
{text}""",
        "technical": """Perform a technical analysis of this text:
- Identify technical terms and concepts
- Note any specifications or requirements
- Extract actionable items

Text:
{text}""",
    }
)

SUMMARIZATION_PROMPTS = PromptTemplate(
    name="summarization",
    description="Prompts for summarizing content",
    variants={
        "control": "Summarize:\n\n{text}",
        "concise": "TL;DR in 2-3 sentences: {text}",
        "detailed": """Provide a comprehensive summary of the following text that:
- Captures all main points
- Preserves important details
- Maintains logical flow
- Is about 1/4 the length of the original

Text:
{text}

Summary:""",
        "structured": """Summarize the text with this structure:
## Overview
[1-2 sentence overview]

## Key Points
- Point 1
- Point 2
- Point 3

## Conclusion
[Main takeaway]

Text:
{text}""",
        "executive": """Write an executive summary suitable for busy decision-makers:
- Lead with the most important conclusion
- Include only essential details
- Keep under 100 words

Text:
{text}""",
    }
)

ANALYSIS_PROMPTS = PromptTemplate(
    name="analysis",
    description="Prompts for analyzing documents (e.g., security review)",
    variants={
        "control": """Analyze this document for issues:

{document}

Analysis:""",
        "concise": "List all issues in: {document}",
        "detailed": """Perform a thorough analysis of the following document.

For each issue found, provide:
1. Description of the issue
2. Severity (Critical/High/Medium/Low)
3. Location in the document
4. Potential impact
5. Recommended fix

Document:
{document}

Detailed analysis:""",
        "security": """You are a security expert reviewing this document for vulnerabilities.

Check for:
- Authentication/authorization issues
- Input validation problems
- Data exposure risks
- Configuration weaknesses
- Compliance violations

Document:
{document}

Security analysis:""",
        "checklist": """Review this document against the following checklist:
[ ] No hardcoded secrets
[ ] Proper input validation
[ ] Secure defaults
[ ] Error handling
[ ] Access controls
[ ] Logging/monitoring

Document:
{document}

Checklist results and findings:""",
    }
)

VALIDATION_PROMPTS = PromptTemplate(
    name="validation",
    description="Prompts for validating/checking content",
    variants={
        "control": """Check if this is correct and complete:

{content}

Validation result:""",
        "concise": "Is this correct? Issues if any: {content}",
        "detailed": """Validate the following content for:
1. Correctness - Is it factually/logically correct?
2. Completeness - Does it fully address the requirements?
3. Quality - Does it meet quality standards?

Content to validate:
{content}

Original task:
{task}

Validation (respond with PASS or FAIL, then explanation):""",
        "strict": """You are a strict validator. Find ANY issues with:

{content}

Requirements:
{task}

Be thorough. Even minor issues should be flagged.
Response format: PASS/FAIL followed by list of issues (if any):""",
        "lenient": """Review this content. Only flag significant issues that would affect usability:

{content}

Major issues only (ignore style/formatting):""",
    }
)


# =============================================================================
# Prompt Registry
# =============================================================================

PROMPT_REGISTRY: Dict[str, PromptTemplate] = {
    "generation": GENERATION_PROMPTS,
    "critique": CRITIQUE_PROMPTS,
    "refinement": REFINEMENT_PROMPTS,
    "extraction": EXTRACTION_PROMPTS,
    "summarization": SUMMARIZATION_PROMPTS,
    "analysis": ANALYSIS_PROMPTS,
    "validation": VALIDATION_PROMPTS,
}


def get_prompt(name: str) -> PromptTemplate:
    """Get a prompt template by name."""
    if name not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown prompt template '{name}'. "
                        f"Available: {list(PROMPT_REGISTRY.keys())}")
    return PROMPT_REGISTRY[name]


def register_prompt(template: PromptTemplate) -> None:
    """Register a custom prompt template."""
    PROMPT_REGISTRY[template.name] = template


def list_prompts() -> List[str]:
    """List all registered prompt templates."""
    return list(PROMPT_REGISTRY.keys())


# =============================================================================
# A/B Test Configuration
# =============================================================================

@dataclass
class ABTestConfig:
    """
    Configuration for an A/B test experiment.
    
    Usage:
        config = ABTestConfig(
            name="critique_style_test",
            prompt_name="critique",
            variants=["control", "detailed", "structured"],
            iterations_per_variant=20,
        )
    """
    name: str
    prompt_name: str
    variants: List[str]
    iterations_per_variant: int = 20
    description: str = ""
    
    def total_iterations(self) -> int:
        """Total iterations across all variants."""
        return len(self.variants) * self.iterations_per_variant


# Pre-defined A/B tests
PREDEFINED_AB_TESTS = {
    "generation_style": ABTestConfig(
        name="generation_style",
        prompt_name="generation",
        variants=["control", "concise", "detailed", "cot"],
        description="Compare different generation prompt styles",
    ),
    "critique_depth": ABTestConfig(
        name="critique_depth",
        prompt_name="critique",
        variants=["control", "concise", "detailed"],
        description="Compare critique prompt verbosity",
    ),
    "extraction_format": ABTestConfig(
        name="extraction_format",
        prompt_name="extraction",
        variants=["control", "structured", "technical"],
        description="Compare extraction output formats",
    ),
    "validation_strictness": ABTestConfig(
        name="validation_strictness",
        prompt_name="validation",
        variants=["control", "strict", "lenient"],
        description="Compare validation strictness levels",
    ),
}


def get_ab_test(name: str) -> ABTestConfig:
    """Get a pre-defined A/B test configuration."""
    if name not in PREDEFINED_AB_TESTS:
        raise ValueError(f"Unknown A/B test '{name}'. "
                        f"Available: {list(PREDEFINED_AB_TESTS.keys())}")
    return PREDEFINED_AB_TESTS[name]
