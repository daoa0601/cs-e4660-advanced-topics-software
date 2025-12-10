"""
Workflow-specific experiment configurations.

Contains:
- run_verbosity_experiment()
- run_context_experiment()
- run_react_experiment()
- run_multiturn_experiment()
- run_self_correcting_experiment()
- run_document_experiment()
- run_rag_experiment()
"""

from ..config import (
    DEFAULT_ITERATIONS,
    DELAY_BETWEEN_CALLS,
    VERBOSITY_QUERIES,
    SHORT_CONTEXT,
    LONG_CONTEXT,
    TECHNICAL_DOCUMENTS,
)
from ..pipeline import get_pipeline
from .core import run_workflow_experiment, DEFAULT_WORKERS


def run_verbosity_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the verbosity tax experiment (concise vs CoT vs hybrid)."""
    pipeline_configs = {
        "concise": (get_pipeline("verbosity_concise"), VERBOSITY_QUERIES),
        "cot": (get_pipeline("verbosity_cot"), VERBOSITY_QUERIES),
        "hybrid_cot": (get_pipeline("hybrid_cot"), VERBOSITY_QUERIES),
    }
    return run_workflow_experiment(
        workflow="verbosity",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="linear",
        experiment_name="Verbosity",
    )


def run_context_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the context length experiment."""
    pipeline_configs = {
        "short": (get_pipeline("context_short"), [SHORT_CONTEXT]),
        "long": (get_pipeline("context_long"), [LONG_CONTEXT]),
    }
    return run_workflow_experiment(
        workflow="context",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="linear",
        experiment_name="Context Length",
    )


def run_react_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the ReAct agent experiment."""
    research_queries = [
        "What are the main causes of climate change and what can be done about it?",
        "How does machine learning differ from traditional programming?",
        "What factors should I consider when choosing a programming language?",
        "What are the pros and cons of remote work?",
        "How do vaccines work to protect against diseases?",
    ]
    pipeline_configs = {
        "react": (get_pipeline("react_research"), research_queries),
        "react_hybrid": (get_pipeline("react_hybrid"), research_queries),
    }
    return run_workflow_experiment(
        workflow="react",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="react",
        experiment_name="ReAct Agent",
    )


def run_multiturn_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the multi-turn conversation experiment."""
    initial_queries = [
        "Tell me about renewable energy sources.",
        "Explain how neural networks learn.",
        "What is the history of the internet?",
        "How do electric vehicles work?",
        "Describe the water cycle.",
    ]
    pipeline_configs = {
        "3_turn": (get_pipeline("multiturn_3"), initial_queries),
        "5_turn": (get_pipeline("multiturn_5"), initial_queries),
    }
    result = run_workflow_experiment(
        workflow="multiturn",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="multiturn",
        experiment_name="Multi-Turn Conversation",
    )
    if result.get("5_turn"):
        print("\n  Context token growth tracked - see analysis notebook for details")
    return result


def run_self_correcting_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run the self-correcting agent experiment."""
    coding_tasks = [
        "Write a Python function to check if a string is a palindrome.",
        "Create a SQL query to find the top 5 customers by total purchase amount.",
        "Write a regular expression to validate email addresses.",
        "Create a function to find the nth Fibonacci number efficiently.",
        "Write code to reverse a linked list.",
    ]
    pipeline_configs = {
        "self_correct": (get_pipeline("self_correcting"), coding_tasks),
        "self_correct_hybrid": (get_pipeline("self_correcting_hybrid"), coding_tasks),
    }
    return run_workflow_experiment(
        workflow="self_correcting",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="self_correcting",
        experiment_name="Self-Correcting Agent",
    )


def run_document_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run document analysis experiment with different pipeline strategies."""
    # Transform documents into query format
    doc_queries = [
        f"Document: {doc['title']}\nType: {doc['type']}\n\n{doc['content']}"
        for doc in TECHNICAL_DOCUMENTS
    ]
    pipeline_configs = {
        "doc_analysis_simple": (get_pipeline("doc_analysis_simple"), doc_queries),
        "doc_analysis_thorough": (get_pipeline("doc_analysis_thorough"), doc_queries),
        "doc_analysis_iterative": (get_pipeline("doc_analysis_iterative"), doc_queries),
        "doc_analysis_hybrid": (get_pipeline("doc_analysis_hybrid"), doc_queries),
    }
    return run_workflow_experiment(
        workflow="document",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="linear",
        experiment_name="Document Analysis",
    )


def run_rag_experiment(
    model: str,
    iterations: int = DEFAULT_ITERATIONS,
    delay: float = DELAY_BETWEEN_CALLS,
    streaming: bool = False,
    use_llm_eval: bool = False,
    parallel: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    """Run RAG pipeline experiment with different retrieval/verification strategies."""
    rag_queries = [
        "How do efficient Transformer architectures address the quadratic memory complexity of self-attention?",
        "Compare different approaches to relative positional encoding in long-sequence modeling.",
        "What are the specific challenges and solutions for applying Transformers to non-text domains like 3D segmentation or music?",
        "Explain the role of reinforcement learning in recent LLM alignment and optimization techniques.",
        "How does retrieval-augmented generation (RAG) technically mitigate hallucinations compared to standard parametric knowledge?",
    ]
    pipeline_configs = {
        "rag_basic": (get_pipeline("rag_basic"), rag_queries),
        "rag_verified": (get_pipeline("rag_verified"), rag_queries),
        "rag_hybrid": (get_pipeline("rag_hybrid"), rag_queries),
    }
    return run_workflow_experiment(
        workflow="rag",
        pipeline_configs=pipeline_configs,
        model=model,
        iterations=iterations,
        delay=delay,
        streaming=streaming,
        use_llm_eval=use_llm_eval,
        parallel=parallel,
        workers=workers,
        pipeline_type="rag",
        experiment_name="RAG Pipeline",
    )
