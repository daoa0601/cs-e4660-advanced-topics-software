"""
LLM Cost Decomposition Platform

A platform for granular cost tracking of complex LLM workflows including:
- Multi-stage pipelines with per-stage cost attribution
- Multi-model hybrid pipelines
- Agentic patterns (ReAct, multi-turn, self-correcting)
- Document analysis workflows
- A/B testing for prompt engineering
- Streaming metrics (TTFT, throughput)
- Parallel execution

Modules:
- config: Model pricing, prompt templates with A/B variants, test data
- clients: Vertex AI API client with streaming
- pipelines: Pipeline orchestration (linear, agentic, document)
- evaluation: Quality assessment (automated and LLM-based)
- db: Thread-safe database operations with WAL mode
- experiments: A/B testing and experiment runners
- utils: Cost calculations
"""

__version__ = "1.0.0"
