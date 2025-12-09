"""
Agentic pipeline classes.

Contains:
- ReActPipeline: Reasoning + Acting loop
- MultiTurnPipeline: Multi-turn conversation with context tracking
- SelfCorrectingPipeline: Generate-validate-fix loop
"""

from dataclasses import dataclass
from typing import Optional, Callable

from ..clients import call_model, call_model_with_history
from ..cost_calculator import calculate_cost
from ..config import get_model_id
from .base import StageType, LoopTermination, StageResult, PipelineResult


@dataclass
class ReActPipeline:
    """
    ReAct (Reasoning + Acting) loop pipeline.

    Pattern: Think -> Act -> Observe -> Think -> ... -> Final Answer
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
            # Pass context_tokens for tiered pricing (>200K triggers long-context rates)
            turn_cost = calculate_cost(
                response.input_tokens,
                response.output_tokens,
                model,
                context_tokens=response.input_tokens  # Context size for tier detection
            )

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

    Pattern: Generate -> Validate -> Fix (if needed) -> Validate -> ... -> Pass/MaxRetries
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
