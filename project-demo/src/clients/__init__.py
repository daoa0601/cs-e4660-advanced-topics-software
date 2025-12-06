"""
API clients module.

Uses the google-genai SDK with Vertex AI backend for Gemini model access.
ADC (Application Default Credentials) is used for authentication.
"""

from .genai_client import (
    StreamingMetrics,
    ModelResponse,
    call_model,
    call_model_with_history,
    test_connection,
    test_streaming,
)

__all__ = [
    "StreamingMetrics",
    "ModelResponse",
    "call_model",
    "call_model_with_history",
    "test_connection",
    "test_streaming",
]
