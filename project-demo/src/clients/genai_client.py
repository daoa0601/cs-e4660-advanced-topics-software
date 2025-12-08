"""
Google GenAI Gemini Client with ADC Support.

This module provides the primary interface for interacting with Gemini models
using the google-genai SDK with Vertex AI backend and Application Default
Credentials (ADC).

Features:
- Automatic ADC authentication (no API key needed)
- Streaming support with TTFT metrics
- Multi-turn conversation support
- Automatic retry with exponential backoff
- Compatible response interface with legacy vertex.py
"""

import time
import functools
from dataclasses import dataclass
from typing import Optional, List, Dict, Callable, TypeVar

from google import genai
from google.genai import types

from ..config import GCP_PROJECT_ID, GCP_REGION, get_model_id
from ..logging_config import get_logger

logger = get_logger(__name__)

# Type variable for generic retry decorator
T = TypeVar('T')


# Retry configuration
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0  # seconds
RETRY_MAX_DELAY = 10.0  # seconds
RETRY_BACKOFF_FACTOR = 2.0


def with_retry(
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    backoff_factor: float = RETRY_BACKOFF_FACTOR,
    retryable_exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator that adds retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        backoff_factor: Multiplier for delay after each retry
        retryable_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = base_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    error_str = str(e).lower()

                    # Check if error is retryable
                    is_rate_limit = "429" in str(e) or "rate" in error_str or "quota" in error_str
                    is_transient = "503" in str(e) or "timeout" in error_str or "unavailable" in error_str

                    if attempt == max_attempts:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
                        raise

                    if is_rate_limit or is_transient:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        # Non-retryable error, raise immediately
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise

            # Should not reach here, but just in case
            raise last_exception
        return wrapper
    return decorator


@dataclass
class StreamingMetrics:
    """Metrics from streaming response."""
    time_to_first_token_ms: int  # Time until first chunk received
    total_latency_ms: int        # Total time for full response
    tokens_per_second: float     # Output throughput
    chunk_count: int             # Number of streamed chunks


@dataclass
class ModelResponse:
    """Response from a model call."""
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    model: str
    success: bool = True
    error_message: Optional[str] = None
    # Streaming metrics (only populated if streaming=True)
    streaming_metrics: Optional[StreamingMetrics] = None


# Module-level client instance
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """Get or create the GenAI client with Vertex AI backend."""
    global _client
    if _client is None:
        if not GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID not set. Check your .env file.")
        _client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_REGION
        )
    return _client


def call_model(prompt: str, model: str, streaming: bool = False) -> ModelResponse:
    """
    Call a Gemini model and return response with metrics.
    
    Args:
        prompt: The input prompt to send to the model
        model: Model identifier (e.g., 'flash', 'pro')
        streaming: If True, use streaming API and capture TTFT metrics
    
    Returns:
        ModelResponse with text, token counts, latency, and optional streaming metrics
    """
    client = _get_client()
    model_id = get_model_id(model)
    
    try:
        if streaming:
            return _call_model_streaming(client, prompt, model_id)
        else:
            return _call_model_sync(client, prompt, model_id)
        
    except Exception as e:
        return ModelResponse(
            text="",
            input_tokens=0,
            output_tokens=0,
            latency_ms=0,
            model=model_id,
            success=False,
            error_message=str(e),
        )


@with_retry()
def _call_model_sync(client: genai.Client, prompt: str, model_id: str) -> ModelResponse:
    """Synchronous (non-streaming) model call with automatic retry."""
    logger.debug(f"Calling {model_id} (sync) with {len(prompt)} chars")
    start_time = time.perf_counter()

    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
    )

    end_time = time.perf_counter()
    latency_ms = int((end_time - start_time) * 1000)

    # Extract usage metadata
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else 0
    output_tokens = usage.candidates_token_count if usage else 0

    logger.debug(f"Response: {input_tokens} in, {output_tokens} out, {latency_ms}ms")

    return ModelResponse(
        text=response.text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        model=model_id,
        success=True,
    )


@with_retry()
def _call_model_streaming(
    client: genai.Client, prompt: str, model_id: str
) -> ModelResponse:
    """Streaming model call with TTFT metrics and automatic retry."""
    logger.debug(f"Calling {model_id} (streaming) with {len(prompt)} chars")
    start_time = time.perf_counter()
    first_token_time = None
    chunks = []
    chunk_count = 0

    # Use streaming generation
    response_stream = client.models.generate_content_stream(
        model=model_id,
        contents=prompt,
    )
    
    for chunk in response_stream:
        if first_token_time is None and chunk.text:
            first_token_time = time.perf_counter()
        chunks.append(chunk)
        chunk_count += 1
    
    end_time = time.perf_counter()
    
    total_latency_ms = int((end_time - start_time) * 1000)
    ttft_ms = (
        int((first_token_time - start_time) * 1000) 
        if first_token_time else total_latency_ms
    )
    
    full_text = "".join(chunk.text for chunk in chunks if chunk.text)
    
    # Get usage from last chunk
    usage = chunks[-1].usage_metadata if chunks else None
    input_tokens = usage.prompt_token_count if usage else 0
    output_tokens = usage.candidates_token_count if usage else 0
    
    duration_seconds = end_time - start_time
    tokens_per_second = output_tokens / duration_seconds if duration_seconds > 0 else 0
    
    streaming_metrics = StreamingMetrics(
        time_to_first_token_ms=ttft_ms,
        total_latency_ms=total_latency_ms,
        tokens_per_second=round(tokens_per_second, 2),
        chunk_count=chunk_count,
    )

    logger.debug(
        f"Response: {input_tokens} in, {output_tokens} out, "
        f"TTFT={ttft_ms}ms, total={total_latency_ms}ms"
    )

    return ModelResponse(
        text=full_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=total_latency_ms,
        model=model_id,
        success=True,
        streaming_metrics=streaming_metrics,
    )


def call_model_with_history(
    messages: List[Dict], 
    model: str,
    streaming: bool = False,
) -> ModelResponse:
    """
    Call model with conversation history for multi-turn conversations.
    
    Args:
        messages: List of {"role": "user"|"model", "content": str}
        model: Model identifier
        streaming: Use streaming API
    
    Returns:
        ModelResponse
    """
    client = _get_client()
    model_id = get_model_id(model)
    
    try:
        # Convert messages to genai format
        contents = []
        for msg in messages:
            contents.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )
        
        start_time = time.perf_counter()
        
        if streaming:
            first_token_time = None
            chunks = []
            chunk_count = 0
            
            response_stream = client.models.generate_content_stream(
                model=model_id,
                contents=contents,
            )
            
            for chunk in response_stream:
                if first_token_time is None and chunk.text:
                    first_token_time = time.perf_counter()
                chunks.append(chunk)
                chunk_count += 1
            
            end_time = time.perf_counter()
            full_text = "".join(c.text for c in chunks if c.text)
            usage = chunks[-1].usage_metadata if chunks else None
            
            ttft_ms = (
                int((first_token_time - start_time) * 1000) 
                if first_token_time else 0
            )
            total_latency_ms = int((end_time - start_time) * 1000)
            
            input_tokens = usage.prompt_token_count if usage else 0
            output_tokens = usage.candidates_token_count if usage else 0
            
            tokens_per_second = (
                output_tokens / (end_time - start_time) 
                if (end_time - start_time) > 0 else 0
            )
            
            return ModelResponse(
                text=full_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=total_latency_ms,
                model=model_id,
                success=True,
                streaming_metrics=StreamingMetrics(
                    time_to_first_token_ms=ttft_ms,
                    total_latency_ms=total_latency_ms,
                    tokens_per_second=round(tokens_per_second, 2),
                    chunk_count=chunk_count,
                ),
            )
        else:
            response = client.models.generate_content(
                model=model_id,
                contents=contents,
            )
            end_time = time.perf_counter()
            
            usage = response.usage_metadata
            return ModelResponse(
                text=response.text,
                input_tokens=usage.prompt_token_count if usage else 0,
                output_tokens=usage.candidates_token_count if usage else 0,
                latency_ms=int((end_time - start_time) * 1000),
                model=model_id,
                success=True,
            )
            
    except Exception as e:
        return ModelResponse(
            text="",
            input_tokens=0,
            output_tokens=0,
            latency_ms=0,
            model=model_id,
            success=False,
            error_message=str(e),
        )


def test_connection() -> bool:
    """Test the Gemini connection with a minimal call."""
    try:
        response = call_model("Say 'hello' in one word.", "flash")
        return response.success
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False


def test_streaming() -> bool:
    """Test streaming API."""
    try:
        response = call_model("Count from 1 to 5.", "flash", streaming=True)
        if response.success and response.streaming_metrics:
            print(f"TTFT: {response.streaming_metrics.time_to_first_token_ms}ms")
            print(f"Total: {response.streaming_metrics.total_latency_ms}ms")
            print(f"Throughput: {response.streaming_metrics.tokens_per_second} tokens/sec")
        return response.success
    except Exception as e:
        print(f"Streaming test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing GenAI Gemini connection (using ADC)...")
    if test_connection():
        print("✓ Sync connection successful!")
    else:
        print("✗ Connection failed.")
    
    print("\nTesting streaming...")
    if test_streaming():
        print("✓ Streaming successful!")
    else:
        print("✗ Streaming failed.")
