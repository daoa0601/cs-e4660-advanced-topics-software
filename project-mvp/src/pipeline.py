"""
Pipeline orchestrator for multi-stage LLM workflows.

Supports:
- Multi-model stages (use different models per stage)
- Linear pipelines (stage1 → stage2 → stage3)
- Agentic patterns (ReAct loops, multi-turn, self-correcting)
- Streaming with TTFT metrics
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import re

from .vertex_client import call_model, call_model_with_history, ModelResponse, StreamingMetrics
from .cost_calculator import calculate_cost
from .config import get_model_id


class StageType(Enum):
    """Types of pipeline stages."""
    GENERATION = "generation"
    CRITIQUE = "critique"
    REFINEMENT = "refinement"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    EVALUATION = "evaluation"
    # Agentic types
    THINKING = "thinking"       # ReAct: reasoning step
    ACTION = "action"           # ReAct: tool/action decision
    OBSERVATION = "observation" # ReAct: process results
    VALIDATION = "validation"   # Self-correcting: check output
    CONVERSATION = "conversation"  # Multi-turn


class LoopTermination(Enum):
    """Reasons for loop termination."""
    MAX_ITERATIONS = "max_iterations"
    CONFIDENCE_REACHED = "confidence_reached"
    VALIDATION_PASSED = "validation_passed"
    ERROR = "error"


@dataclass
class StageResult:
    """Result from a single pipeline stage."""
    stage_name: str
    stage_type: StageType
    stage_order: int
    input_text: str
    output_text: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: int
    model: str
    success: bool = True
    error_message: Optional[str] = None
    # Streaming metrics
    time_to_first_token_ms: Optional[int] = None
    tokens_per_second: Optional[float] = None
    # Loop metadata
    iteration: Optional[int] = None
    turn: Optional[int] = None


@dataclass
class PipelineResult:
    """Complete result from a pipeline execution."""
    pipeline_name: str
    stages: list[StageResult]
    final_output: str
    total_cost: float
    total_latency_ms: int
    total_input_tokens: int
    total_output_tokens: int
    success: bool = True
    # Loop metadata
    iterations: int = 1
    termination_reason: Optional[LoopTermination] = None
    # Multi-turn metadata
    turns: int = 1
    context_tokens_by_turn: list[int] = field(default_factory=list)
    
    @property
    def stage_costs(self) -> dict[str, float]:
        """Get cost breakdown by stage."""
        return {s.stage_name: s.cost for s in self.stages}
    
    @property
    def cost_by_stage_type(self) -> dict[str, float]:
        """Get cost breakdown by stage type."""
        costs = {}
        for s in self.stages:
            stage_type = s.stage_type.value
            costs[stage_type] = costs.get(stage_type, 0) + s.cost
        return costs
    
    @property
    def cost_by_model(self) -> dict[str, float]:
        """Get cost breakdown by model."""
        costs = {}
        for s in self.stages:
            costs[s.model] = costs.get(s.model, 0) + s.cost
        return costs
    
    @property
    def avg_ttft_ms(self) -> Optional[float]:
        """Average time to first token across stages."""
        ttfts = [s.time_to_first_token_ms for s in self.stages if s.time_to_first_token_ms]
        return sum(ttfts) / len(ttfts) if ttfts else None


@dataclass
class PipelineStage:
    """Definition of a pipeline stage."""
    name: str
    stage_type: StageType
    prompt_template: str
    model_override: Optional[str] = None
    
    def build_prompt(self, **kwargs) -> str:
        """Build the prompt from template and variables."""
        return self.prompt_template.format(**kwargs)


@dataclass 
class Pipeline:
    """A multi-stage LLM pipeline."""
    name: str
    description: str
    stages: list[PipelineStage]
    
    def execute(
        self, 
        initial_input: str, 
        model: str,
        context: Optional[dict] = None,
        streaming: bool = False,
    ) -> PipelineResult:
        """Execute the pipeline with the given input."""
        context = context or {}
        stage_results = []
        current_input = initial_input
        
        total_cost = 0
        total_latency = 0
        total_input_tokens = 0
        total_output_tokens = 0
        
        for i, stage in enumerate(self.stages):
            stage_model = stage.model_override or model
            
            prompt = stage.build_prompt(
                input=current_input,
                initial_input=initial_input,
                **context
            )
            
            response = call_model(prompt, stage_model, streaming=streaming)
            
            stage_cost = calculate_cost(
                response.input_tokens,
                response.output_tokens,
                stage_model
            )
            
            stage_result = StageResult(
                stage_name=stage.name,
                stage_type=stage.stage_type,
                stage_order=i + 1,
                input_text=prompt,
                output_text=response.text,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost=stage_cost,
                latency_ms=response.latency_ms,
                model=get_model_id(stage_model),
                success=response.success,
                error_message=response.error_message,
                time_to_first_token_ms=response.streaming_metrics.time_to_first_token_ms if response.streaming_metrics else None,
                tokens_per_second=response.streaming_metrics.tokens_per_second if response.streaming_metrics else None,
            )
            stage_results.append(stage_result)
            
            total_cost += stage_cost
            total_latency += response.latency_ms
            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens
            
            if response.success:
                current_input = response.text
            else:
                return PipelineResult(
                    pipeline_name=self.name,
                    stages=stage_results,
                    final_output="",
                    total_cost=total_cost,
                    total_latency_ms=total_latency,
                    total_input_tokens=total_input_tokens,
                    total_output_tokens=total_output_tokens,
                    success=False,
                )
        
        return PipelineResult(
            pipeline_name=self.name,
            stages=stage_results,
            final_output=current_input,
            total_cost=total_cost,
            total_latency_ms=total_latency,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            success=True,
        )


# =============================================================================
# Agentic Pipeline Classes
# =============================================================================

@dataclass
class ReActPipeline:
    """
    ReAct (Reasoning + Acting) loop pipeline.
    
    Pattern: Think → Act → Observe → Think → ... → Final Answer
    """
    name: str
    description: str
    max_iterations: int = 5
    think_model: str = "flash"
    act_model: str = "flash"
    
    def execute(
        self,
        query: str,
        model: str,
        streaming: bool = False,
    ) -> PipelineResult:
        """Execute ReAct loop until confident or max iterations."""
        stage_results = []
        total_cost = 0
        total_latency = 0
        total_input_tokens = 0
        total_output_tokens = 0
        
        context = f"Question: {query}\n\n"
        termination_reason = LoopTermination.MAX_ITERATIONS
        
        for iteration in range(1, self.max_iterations + 1):
            # THINK stage
            think_prompt = f"""{context}
Iteration {iteration}/{self.max_iterations}

Think step by step about how to answer this question.
If you have enough information, say "FINAL ANSWER:" followed by your answer.
If you need more information, say "I NEED TO:" followed by what you need to find out.

Your thinking:"""
            
            think_response = call_model(think_prompt, self.think_model, streaming)
            think_cost = calculate_cost(think_response.input_tokens, think_response.output_tokens, self.think_model)
            
            stage_results.append(StageResult(
                stage_name=f"think_{iteration}",
                stage_type=StageType.THINKING,
                stage_order=len(stage_results) + 1,
                input_text=think_prompt,
                output_text=think_response.text,
                input_tokens=think_response.input_tokens,
                output_tokens=think_response.output_tokens,
                cost=think_cost,
                latency_ms=think_response.latency_ms,
                model=get_model_id(self.think_model),
                success=think_response.success,
                iteration=iteration,
                time_to_first_token_ms=think_response.streaming_metrics.time_to_first_token_ms if think_response.streaming_metrics else None,
                tokens_per_second=think_response.streaming_metrics.tokens_per_second if think_response.streaming_metrics else None,
            ))
            
            total_cost += think_cost
            total_latency += think_response.latency_ms
            total_input_tokens += think_response.input_tokens
            total_output_tokens += think_response.output_tokens
            
            # Check for final answer
            if "FINAL ANSWER:" in think_response.text.upper():
                termination_reason = LoopTermination.CONFIDENCE_REACHED
                final_output = think_response.text.split("FINAL ANSWER:")[-1].strip()
                break
            
            # ACT stage - simulate action/tool use
            act_prompt = f"""Based on this thinking:
{think_response.text}

Simulate gathering the needed information. Provide a brief observation of what you found.
Start with "OBSERVATION:" followed by the relevant information."""
            
            act_response = call_model(act_prompt, self.act_model, streaming)
            act_cost = calculate_cost(act_response.input_tokens, act_response.output_tokens, self.act_model)
            
            stage_results.append(StageResult(
                stage_name=f"act_{iteration}",
                stage_type=StageType.ACTION,
                stage_order=len(stage_results) + 1,
                input_text=act_prompt,
                output_text=act_response.text,
                input_tokens=act_response.input_tokens,
                output_tokens=act_response.output_tokens,
                cost=act_cost,
                latency_ms=act_response.latency_ms,
                model=get_model_id(self.act_model),
                success=act_response.success,
                iteration=iteration,
                time_to_first_token_ms=act_response.streaming_metrics.time_to_first_token_ms if act_response.streaming_metrics else None,
                tokens_per_second=act_response.streaming_metrics.tokens_per_second if act_response.streaming_metrics else None,
            ))
            
            total_cost += act_cost
            total_latency += act_response.latency_ms
            total_input_tokens += act_response.input_tokens
            total_output_tokens += act_response.output_tokens
            
            # Update context for next iteration
            context += f"\nThought {iteration}: {think_response.text}\n"
            context += f"Observation {iteration}: {act_response.text}\n"
            
            final_output = act_response.text
        
        return PipelineResult(
            pipeline_name=self.name,
            stages=stage_results,
            final_output=final_output if 'final_output' in dir() else "",
            total_cost=total_cost,
            total_latency_ms=total_latency,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            success=True,
            iterations=iteration,
            termination_reason=termination_reason,
        )


@dataclass
class MultiTurnPipeline:
    """
    Multi-turn conversation pipeline with context accumulation tracking.
    
    Tracks how costs grow as conversation history accumulates.
    """
    name: str
    description: str
    turns: list[str]  # List of user messages to simulate
    
    def execute(
        self,
        initial_query: str,
        model: str,
        streaming: bool = False,
    ) -> PipelineResult:
        """Execute multi-turn conversation."""
        stage_results = []
        total_cost = 0
        total_latency = 0
        total_input_tokens = 0
        total_output_tokens = 0
        context_tokens_by_turn = []
        
        # Build conversation messages
        messages = [{"role": "user", "content": initial_query}]
        all_turns = [initial_query] + self.turns
        
        for turn_num, user_message in enumerate(all_turns, 1):
            if turn_num > 1:
                messages.append({"role": "user", "content": user_message})
            
            response = call_model_with_history(messages, model, streaming)
            turn_cost = calculate_cost(response.input_tokens, response.output_tokens, model)
            
            stage_results.append(StageResult(
                stage_name=f"turn_{turn_num}",
                stage_type=StageType.CONVERSATION,
                stage_order=turn_num,
                input_text=user_message,
                output_text=response.text,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost=turn_cost,
                latency_ms=response.latency_ms,
                model=get_model_id(model),
                success=response.success,
                turn=turn_num,
                time_to_first_token_ms=response.streaming_metrics.time_to_first_token_ms if response.streaming_metrics else None,
                tokens_per_second=response.streaming_metrics.tokens_per_second if response.streaming_metrics else None,
            ))
            
            total_cost += turn_cost
            total_latency += response.latency_ms
            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens
            context_tokens_by_turn.append(response.input_tokens)
            
            # Add assistant response to history
            if response.success:
                messages.append({"role": "model", "content": response.text})
        
        return PipelineResult(
            pipeline_name=self.name,
            stages=stage_results,
            final_output=stage_results[-1].output_text if stage_results else "",
            total_cost=total_cost,
            total_latency_ms=total_latency,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            success=True,
            turns=len(all_turns),
            context_tokens_by_turn=context_tokens_by_turn,
        )


@dataclass
class SelfCorrectingPipeline:
    """
    Self-correcting pipeline with validation loop.
    
    Pattern: Generate → Validate → Fix (if needed) → Validate → ... → Pass/MaxRetries
    """
    name: str
    description: str
    max_retries: int = 3
    generate_model: str = "flash"
    validate_model: str = "flash"
    validator: Optional[Callable[[str], tuple[bool, str]]] = None  # Custom validator function
    
    def execute(
        self,
        task: str,
        model: str,
        streaming: bool = False,
    ) -> PipelineResult:
        """Execute self-correcting loop."""
        stage_results = []
        total_cost = 0
        total_latency = 0
        total_input_tokens = 0
        total_output_tokens = 0
        
        gen_model = self.generate_model or model
        val_model = self.validate_model or model
        
        termination_reason = LoopTermination.MAX_ITERATIONS
        current_output = ""
        validation_feedback = ""
        
        for attempt in range(1, self.max_retries + 1):
            # GENERATE stage
            if attempt == 1:
                gen_prompt = f"""Task: {task}

Provide your solution:"""
            else:
                gen_prompt = f"""Task: {task}

Your previous attempt:
{current_output}

Validation feedback:
{validation_feedback}

Please fix the issues and provide an improved solution:"""
            
            gen_response = call_model(gen_prompt, gen_model, streaming)
            gen_cost = calculate_cost(gen_response.input_tokens, gen_response.output_tokens, gen_model)
            
            stage_results.append(StageResult(
                stage_name=f"generate_{attempt}",
                stage_type=StageType.GENERATION if attempt == 1 else StageType.REFINEMENT,
                stage_order=len(stage_results) + 1,
                input_text=gen_prompt,
                output_text=gen_response.text,
                input_tokens=gen_response.input_tokens,
                output_tokens=gen_response.output_tokens,
                cost=gen_cost,
                latency_ms=gen_response.latency_ms,
                model=get_model_id(gen_model),
                success=gen_response.success,
                iteration=attempt,
                time_to_first_token_ms=gen_response.streaming_metrics.time_to_first_token_ms if gen_response.streaming_metrics else None,
                tokens_per_second=gen_response.streaming_metrics.tokens_per_second if gen_response.streaming_metrics else None,
            ))
            
            total_cost += gen_cost
            total_latency += gen_response.latency_ms
            total_input_tokens += gen_response.input_tokens
            total_output_tokens += gen_response.output_tokens
            current_output = gen_response.text
            
            # VALIDATE stage
            if self.validator:
                # Use custom validator
                is_valid, validation_feedback = self.validator(current_output)
            else:
                # Use LLM-based validation
                val_prompt = f"""Task: {task}

Solution to validate:
{current_output}

Evaluate this solution:
1. Is it correct and complete? (YES/NO)
2. If NO, what specific issues need to be fixed?

Start your response with "VALID: YES" or "VALID: NO" followed by your explanation."""
                
                val_response = call_model(val_prompt, val_model, streaming)
                val_cost = calculate_cost(val_response.input_tokens, val_response.output_tokens, val_model)
                
                stage_results.append(StageResult(
                    stage_name=f"validate_{attempt}",
                    stage_type=StageType.VALIDATION,
                    stage_order=len(stage_results) + 1,
                    input_text=val_prompt,
                    output_text=val_response.text,
                    input_tokens=val_response.input_tokens,
                    output_tokens=val_response.output_tokens,
                    cost=val_cost,
                    latency_ms=val_response.latency_ms,
                    model=get_model_id(val_model),
                    success=val_response.success,
                    iteration=attempt,
                    time_to_first_token_ms=val_response.streaming_metrics.time_to_first_token_ms if val_response.streaming_metrics else None,
                    tokens_per_second=val_response.streaming_metrics.tokens_per_second if val_response.streaming_metrics else None,
                ))
                
                total_cost += val_cost
                total_latency += val_response.latency_ms
                total_input_tokens += val_response.input_tokens
                total_output_tokens += val_response.output_tokens
                
                is_valid = "VALID: YES" in val_response.text.upper()
                validation_feedback = val_response.text
            
            if is_valid:
                termination_reason = LoopTermination.VALIDATION_PASSED
                break
        
        return PipelineResult(
            pipeline_name=self.name,
            stages=stage_results,
            final_output=current_output,
            total_cost=total_cost,
            total_latency_ms=total_latency,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            success=termination_reason == LoopTermination.VALIDATION_PASSED,
            iterations=attempt,
            termination_reason=termination_reason,
        )


# =============================================================================
# Pre-defined Pipelines
# =============================================================================

# --- Standard Pipelines (from before) ---

VERBOSITY_CONCISE_PIPELINE = Pipeline(
    name="verbosity_concise",
    description="Single-stage concise response",
    stages=[
        PipelineStage(
            name="generate",
            stage_type=StageType.GENERATION,
            prompt_template="Answer the following question in 1-2 sentences:\n\n{input}",
        ),
    ]
)

VERBOSITY_COT_PIPELINE = Pipeline(
    name="verbosity_cot",
    description="Chain-of-thought with self-critique and refinement",
    stages=[
        PipelineStage(
            name="draft",
            stage_type=StageType.GENERATION,
            prompt_template="Think step by step and explain your reasoning:\n\n{input}",
        ),
        PipelineStage(
            name="critique",
            stage_type=StageType.CRITIQUE,
            prompt_template="""Review the following response for accuracy and completeness.
List any errors, gaps, or areas that could be improved.

Original question: {initial_input}

Response to review:
{input}

Critique:""",
        ),
        PipelineStage(
            name="refine",
            stage_type=StageType.REFINEMENT,
            prompt_template="""Based on the critique below, provide an improved response to the original question.

Original question: {initial_input}

Critique:
{input}

Improved response:""",
        ),
    ]
)

# --- Multi-Model Hybrid Pipelines ---

HYBRID_COT_PIPELINE = Pipeline(
    name="hybrid_cot",
    description="CoT with Flash for draft, Pro for critique, Flash for refine",
    stages=[
        PipelineStage(
            name="draft",
            stage_type=StageType.GENERATION,
            prompt_template="Think step by step and explain your reasoning:\n\n{input}",
            model_override="flash",  # Cheap model for initial draft
        ),
        PipelineStage(
            name="critique",
            stage_type=StageType.CRITIQUE,
            prompt_template="""Review the following response for accuracy and completeness.
List any errors, gaps, or areas that could be improved.

Original question: {initial_input}

Response to review:
{input}

Critique:""",
            model_override="pro",  # Smart model for critique
        ),
        PipelineStage(
            name="refine",
            stage_type=StageType.REFINEMENT,
            prompt_template="""Based on the critique below, provide an improved response to the original question.

Original question: {initial_input}

Critique:
{input}

Improved response:""",
            model_override="flash",  # Cheap model for execution
        ),
    ]
)

CONTEXT_SHORT_PIPELINE = Pipeline(
    name="context_short",
    description="Short context summarization",
    stages=[
        PipelineStage(
            name="extract",
            stage_type=StageType.EXTRACTION,
            prompt_template="""Extract the 3 most important facts from this text:

{input}

Key facts:""",
        ),
        PipelineStage(
            name="summarize",
            stage_type=StageType.SUMMARIZATION,
            prompt_template="""Based on these key facts, write a one-paragraph summary:

{input}

Summary:""",
        ),
    ]
)

CONTEXT_LONG_PIPELINE = Pipeline(
    name="context_long",
    description="Long context with extraction, summarization, and evaluation",
    stages=[
        PipelineStage(
            name="extract",
            stage_type=StageType.EXTRACTION,
            prompt_template="""Extract all important facts, figures, and key points from this document:

{input}

Extracted information:""",
        ),
        PipelineStage(
            name="summarize",
            stage_type=StageType.SUMMARIZATION,
            prompt_template="""Create a comprehensive summary from these extracted points:

{input}

Summary:""",
        ),
        PipelineStage(
            name="evaluate",
            stage_type=StageType.EVALUATION,
            prompt_template="""Review this summary for completeness. Does it capture the main points?
If anything important is missing, add it.

Summary to review:
{input}

Final summary with any additions:""",
        ),
    ]
)

# --- Agentic Pipelines ---

REACT_RESEARCH_PIPELINE = ReActPipeline(
    name="react_research",
    description="ReAct loop for research questions with up to 5 iterations",
    max_iterations=5,
    think_model="flash",
    act_model="flash",
)

REACT_HYBRID_PIPELINE = ReActPipeline(
    name="react_hybrid",
    description="ReAct with Pro for thinking, Flash for actions",
    max_iterations=5,
    think_model="pro",
    act_model="flash",
)

MULTITURN_SHORT_PIPELINE = MultiTurnPipeline(
    name="multiturn_3",
    description="3-turn conversation",
    turns=[
        "Can you elaborate on that?",
        "What are the implications?",
    ],
)

MULTITURN_LONG_PIPELINE = MultiTurnPipeline(
    name="multiturn_5",
    description="5-turn conversation with context growth",
    turns=[
        "Tell me more about the first point.",
        "How does that compare to alternatives?",
        "What are the risks involved?",
        "Can you summarize the key takeaways?",
    ],
)

SELF_CORRECTING_PIPELINE = SelfCorrectingPipeline(
    name="self_correcting",
    description="Generate-validate-fix loop with up to 3 retries",
    max_retries=3,
    generate_model="flash",
    validate_model="flash",
)

SELF_CORRECTING_HYBRID_PIPELINE = SelfCorrectingPipeline(
    name="self_correcting_hybrid",
    description="Flash generates, Pro validates",
    max_retries=3,
    generate_model="flash",
    validate_model="pro",
)

# --- Document Analysis Pipelines ---

DOC_ANALYSIS_SIMPLE_PIPELINE = Pipeline(
    name="doc_analysis_simple",
    description="Simple 2-stage document analysis: Extract key info → Identify issues",
    stages=[
        PipelineStage(
            name="extract",
            stage_type=StageType.EXTRACTION,
            prompt_template="""Analyze this technical document and extract the key components, configurations, and logic:

{input}

Provide a structured breakdown of:
1. Main components/functions
2. Data flows
3. External dependencies
4. Security-relevant elements

Extraction:""",
        ),
        PipelineStage(
            name="analyze",
            stage_type=StageType.GENERATION,
            prompt_template="""Based on this technical extraction:

{input}

Identify potential issues including:
- Security vulnerabilities
- Bugs or logic errors
- Misconfigurations
- Best practice violations
- Performance concerns

For each issue, explain:
1. What the issue is
2. Why it's a problem
3. Severity (Critical/High/Medium/Low)

Issues Found:""",
        ),
    ]
)

DOC_ANALYSIS_THOROUGH_PIPELINE = Pipeline(
    name="doc_analysis_thorough",
    description="Thorough 4-stage analysis: Extract → Analyze → Classify → Recommend",
    stages=[
        PipelineStage(
            name="extract",
            stage_type=StageType.EXTRACTION,
            prompt_template="""Analyze this technical document and extract all relevant details:

{input}

Provide a comprehensive breakdown:
1. Document type and purpose
2. Key components and their responsibilities
3. Data handling and storage
4. Authentication/authorization mechanisms
5. External integrations
6. Configuration settings

Detailed Extraction:""",
        ),
        PipelineStage(
            name="analyze",
            stage_type=StageType.GENERATION,
            prompt_template="""Based on this technical extraction:

{input}

Perform a thorough security and quality analysis. Identify ALL potential issues:
- Security vulnerabilities (injection, auth bypass, data exposure, etc.)
- Code quality issues (bugs, race conditions, error handling)
- Configuration problems (hardcoded secrets, permissive settings)
- Architectural concerns (single points of failure, scalability)
- Compliance issues (PCI, GDPR, etc. if applicable)

List every issue found:""",
        ),
        PipelineStage(
            name="classify",
            stage_type=StageType.EVALUATION,
            prompt_template="""Review and classify these identified issues:

{input}

For each issue, provide:
1. Category (Security/Bug/Config/Architecture/Compliance)
2. Severity (Critical/High/Medium/Low)
3. Exploitability (Easy/Medium/Hard)
4. Business Impact

Organize issues by severity, with Critical issues first:

Classified Issues:""",
            model_override="pro",  # Use Pro for better classification
        ),
        PipelineStage(
            name="recommend",
            stage_type=StageType.REFINEMENT,
            prompt_template="""Based on these classified issues:

{input}

Provide actionable remediation recommendations:

For each issue:
1. Specific fix or mitigation
2. Code/config example if applicable
3. Priority for remediation
4. Estimated effort (Quick fix / Moderate / Significant refactor)

Also provide:
- Immediate actions (do today)
- Short-term fixes (this sprint)
- Long-term improvements (roadmap items)

Remediation Plan:""",
        ),
    ]
)

DOC_ANALYSIS_ITERATIVE_PIPELINE = Pipeline(
    name="doc_analysis_iterative",
    description="Iterative analysis with self-review: Analyze → Review → Refine",
    stages=[
        PipelineStage(
            name="initial_analysis",
            stage_type=StageType.GENERATION,
            prompt_template="""You are a senior security engineer reviewing this technical document:

{input}

Perform a comprehensive security and code quality review. Identify all issues including:
- Security vulnerabilities
- Bugs and logic errors  
- Misconfigurations
- Best practice violations

For each issue provide: description, severity, and location in the document.

Initial Analysis:""",
        ),
        PipelineStage(
            name="self_review",
            stage_type=StageType.CRITIQUE,
            prompt_template="""Review this security analysis for completeness and accuracy:

{input}

Check for:
1. False positives - issues that aren't actually problems
2. Missed issues - common vulnerabilities not mentioned
3. Severity accuracy - are ratings appropriate?
4. Missing context - are explanations clear enough?

What issues were missed? What should be corrected?

Review Findings:""",
            model_override="pro",  # Use Pro for thorough review
        ),
        PipelineStage(
            name="refined_analysis",
            stage_type=StageType.REFINEMENT,
            prompt_template="""Based on the self-review feedback:

{input}

Produce a refined, comprehensive analysis that:
1. Removes any false positives identified
2. Adds any missed issues
3. Corrects severity ratings if needed
4. Provides clearer explanations

Final Analysis Report:

## Executive Summary
[Brief overview of findings]

## Critical Issues
[Most severe issues requiring immediate attention]

## High Priority Issues  
[Significant issues to address soon]

## Medium/Low Priority Issues
[Issues to address in normal course]

## Recommendations
[Prioritized action items]

Refined Analysis:""",
        ),
    ]
)

DOC_ANALYSIS_HYBRID_PIPELINE = Pipeline(
    name="doc_analysis_hybrid",
    description="Hybrid analysis: Flash extracts, Pro analyzes and recommends",
    stages=[
        PipelineStage(
            name="extract",
            stage_type=StageType.EXTRACTION,
            prompt_template="""Extract key technical details from this document:

{input}

List:
1. Components and functions
2. Security-relevant code patterns
3. Configuration values
4. Data handling logic

Extraction:""",
            model_override="flash",  # Cheap extraction
        ),
        PipelineStage(
            name="deep_analysis",
            stage_type=StageType.GENERATION,
            prompt_template="""As a senior security expert, analyze these extracted details for vulnerabilities and issues:

{input}

Provide expert-level analysis of:
- Security vulnerabilities with CVE references if applicable
- Attack vectors and exploitability
- Compliance implications
- Risk assessment

Expert Analysis:""",
            model_override="pro",  # Expert analysis with Pro
        ),
        PipelineStage(
            name="remediation",
            stage_type=StageType.REFINEMENT,
            prompt_template="""Based on this security analysis:

{input}

Provide specific, actionable remediation steps with code examples where applicable:

Remediation Guide:""",
            model_override="flash",  # Execution with Flash
        ),
    ]
)


# =============================================================================
# Pipeline Registry
# =============================================================================

PIPELINES = {
    # Standard
    "verbosity_concise": VERBOSITY_CONCISE_PIPELINE,
    "verbosity_cot": VERBOSITY_COT_PIPELINE,
    "context_short": CONTEXT_SHORT_PIPELINE,
    "context_long": CONTEXT_LONG_PIPELINE,
    # Multi-model hybrid
    "hybrid_cot": HYBRID_COT_PIPELINE,
    # Agentic
    "react_research": REACT_RESEARCH_PIPELINE,
    "react_hybrid": REACT_HYBRID_PIPELINE,
    "multiturn_3": MULTITURN_SHORT_PIPELINE,
    "multiturn_5": MULTITURN_LONG_PIPELINE,
    "self_correcting": SELF_CORRECTING_PIPELINE,
    "self_correcting_hybrid": SELF_CORRECTING_HYBRID_PIPELINE,
    # Document Analysis
    "doc_analysis_simple": DOC_ANALYSIS_SIMPLE_PIPELINE,
    "doc_analysis_thorough": DOC_ANALYSIS_THOROUGH_PIPELINE,
    "doc_analysis_iterative": DOC_ANALYSIS_ITERATIVE_PIPELINE,
    "doc_analysis_hybrid": DOC_ANALYSIS_HYBRID_PIPELINE,
}


def get_pipeline(name: str):
    """Get a pipeline by name."""
    if name not in PIPELINES:
        raise ValueError(f"Unknown pipeline: {name}. Available: {list(PIPELINES.keys())}")
    return PIPELINES[name]


def list_pipelines() -> list[dict]:
    """List all available pipelines with their details."""
    result = []
    for name, p in PIPELINES.items():
        if isinstance(p, Pipeline):
            result.append({
                "name": p.name,
                "description": p.description,
                "type": "linear",
                "num_stages": len(p.stages),
                "stages": [s.name for s in p.stages],
                "multi_model": any(s.model_override for s in p.stages),
            })
        elif isinstance(p, ReActPipeline):
            result.append({
                "name": p.name,
                "description": p.description,
                "type": "react",
                "max_iterations": p.max_iterations,
                "stages": ["think", "act"],
                "multi_model": p.think_model != p.act_model,
            })
        elif isinstance(p, MultiTurnPipeline):
            result.append({
                "name": p.name,
                "description": p.description,
                "type": "multiturn",
                "num_turns": len(p.turns) + 1,
                "stages": [f"turn_{i}" for i in range(1, len(p.turns) + 2)],
                "multi_model": False,
            })
        elif isinstance(p, SelfCorrectingPipeline):
            result.append({
                "name": p.name,
                "description": p.description,
                "type": "self_correcting",
                "max_retries": p.max_retries,
                "stages": ["generate", "validate"],
                "multi_model": p.generate_model != p.validate_model,
            })
    return result
