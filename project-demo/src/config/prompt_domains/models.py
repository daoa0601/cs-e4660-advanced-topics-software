"""
Prompt template models.

Contains:
- PromptTemplate: A single prompt template with variables
- DomainConfig: Configuration for a domain
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PromptTemplate:
    """A single prompt template with variables."""
    name: str
    template: str
    variables: Dict[str, List[str]]
    difficulty: str = "medium"  # easy, medium, hard
    expected_output_length: str = "medium"  # short, medium, long

    def generate(self, seed: Optional[int] = None) -> str:
        """Generate a concrete prompt from this template."""
        if seed is not None:
            random.seed(seed)

        prompt = self.template
        for var_name, options in self.variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, random.choice(options))
        return prompt


@dataclass
class DomainConfig:
    """Configuration for a specific domain."""
    name: str
    description: str
    templates: List[PromptTemplate]
    system_prompts: Dict[str, str] = field(default_factory=dict)
    evaluation_criteria: List[str] = field(default_factory=list)

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a specific template by name."""
        for t in self.templates:
            if t.name == name:
                return t
        return None

    def generate_prompts(self, n: int, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate n random prompts from this domain."""
        if seed is not None:
            random.seed(seed)

        prompts = []
        for i in range(n):
            template = random.choice(self.templates)
            prompts.append({
                "domain": self.name,
                "template_name": template.name,
                "prompt": template.generate(seed=seed + i if seed else None),
                "difficulty": template.difficulty,
                "expected_output_length": template.expected_output_length,
            })
        return prompts
