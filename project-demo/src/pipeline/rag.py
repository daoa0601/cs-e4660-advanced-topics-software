"""
RAG (Retrieval-Augmented Generation) pipeline.

Contains:
- RAGPipeline: Multi-stage RAG with simulated retrieval
"""

from dataclasses import dataclass

from ..clients import call_model
from ..cost_calculator import calculate_cost
from ..config import get_model_id
from .base import StageType, StageResult, PipelineResult


@dataclass
class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline with simulated retrieval.

    Stages:
    1. Query Understanding - Parse and classify the query
    2. Retrieval (simulated) - Select k documents from corpus
    3. Context Assembly - Build prompt with retrieved docs
    4. Generation - Generate response with context
    5. Verification (optional) - Check citations
    """
    name: str
    description: str
    retrieval_k: int = 5
    enable_verification: bool = True
    query_model: str = "flash"
    generation_model: str = "flash"
    verification_model: str = "flash"

    # Simulated document corpus for retrieval
    DOCUMENT_CORPUS = [
        {"id": 1, "title": "Machine Learning Basics", "content": "Machine learning is a subset of AI that enables systems to learn from data. Key concepts include supervised learning, unsupervised learning, and reinforcement learning."},
        {"id": 2, "title": "Neural Networks", "content": "Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes that process information."},
        {"id": 3, "title": "Natural Language Processing", "content": "NLP enables computers to understand human language. Techniques include tokenization, named entity recognition, and sentiment analysis."},
        {"id": 4, "title": "Deep Learning", "content": "Deep learning uses multi-layer neural networks. Popular architectures include CNNs for images and RNNs/Transformers for sequences."},
        {"id": 5, "title": "AI Ethics", "content": "AI ethics addresses concerns about bias, fairness, transparency, and accountability in AI systems. Responsible AI development is crucial."},
        {"id": 6, "title": "Computer Vision", "content": "Computer vision enables machines to interpret visual information. Applications include image classification, object detection, and facial recognition."},
        {"id": 7, "title": "Reinforcement Learning", "content": "RL trains agents through trial and error using rewards. Key algorithms include Q-learning, policy gradients, and actor-critic methods."},
        {"id": 8, "title": "Data Preprocessing", "content": "Data preprocessing includes cleaning, normalization, and feature engineering. Quality data is essential for model performance."},
        {"id": 9, "title": "Model Evaluation", "content": "Model evaluation uses metrics like accuracy, precision, recall, and F1-score. Cross-validation helps assess generalization."},
        {"id": 10, "title": "Large Language Models", "content": "LLMs like GPT and BERT are transformer-based models trained on vast text data. They excel at text generation and understanding."},
    ]

    def _simulate_retrieval(self, query: str, k: int) -> list[dict]:
        """Simulate document retrieval by selecting relevant documents."""
        # Simple keyword-based retrieval simulation
        query_words = set(query.lower().split())
        scored_docs = []

        for doc in self.DOCUMENT_CORPUS:
            doc_words = set(doc['content'].lower().split())
            overlap = len(query_words & doc_words)
            scored_docs.append((overlap, doc))

        # Sort by relevance score and take top k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:k]]

    def execute(
        self,
        query: str,
        model: str,
        streaming: bool = False,
    ) -> PipelineResult:
        """Execute RAG pipeline with simulated retrieval."""
        stage_results = []
        total_cost = 0
        total_latency = 0
        total_input_tokens = 0
        total_output_tokens = 0

        # Stage 1: Query Understanding
        query_prompt = f"""Analyze this query and identify the key topics and intent:

Query: {query}

Provide:
1. Main topic(s)
2. Query intent (factual, explanatory, comparative, etc.)
3. Key terms for retrieval

Analysis:"""

        query_response = call_model(query_prompt, self.query_model, streaming)
        query_cost = calculate_cost(query_response.input_tokens, query_response.output_tokens, self.query_model)

        stage_results.append(StageResult(
            stage_name="query_understanding",
            stage_type=StageType.QUERY_UNDERSTANDING,
            stage_order=1,
            input_text=query_prompt,
            output_text=query_response.text,
            input_tokens=query_response.input_tokens,
            output_tokens=query_response.output_tokens,
            cost=query_cost,
            latency_ms=query_response.latency_ms,
            model=get_model_id(self.query_model),
            success=query_response.success,
            time_to_first_token_ms=query_response.streaming_metrics.time_to_first_token_ms if query_response.streaming_metrics else None,
            tokens_per_second=query_response.streaming_metrics.tokens_per_second if query_response.streaming_metrics else None,
        ))

        total_cost += query_cost
        total_latency += query_response.latency_ms
        total_input_tokens += query_response.input_tokens
        total_output_tokens += query_response.output_tokens

        # Stage 2: Simulated Retrieval (no API call, just simulation)
        retrieved_docs = self._simulate_retrieval(query, self.retrieval_k)
        retrieval_summary = "\n".join([
            f"[{doc['id']}] {doc['title']}: {doc['content'][:100]}..."
            for doc in retrieved_docs
        ])

        stage_results.append(StageResult(
            stage_name="retrieval",
            stage_type=StageType.RETRIEVAL,
            stage_order=2,
            input_text=query,
            output_text=retrieval_summary,
            input_tokens=0,  # Simulated - no actual tokens
            output_tokens=0,
            cost=0,  # No API cost for simulated retrieval
            latency_ms=10,  # Simulated latency
            model="simulated",
            success=True,
        ))

        # Stage 3: Context Assembly
        context_docs = "\n\n".join([
            f"Document [{doc['id']}] - {doc['title']}:\n{doc['content']}"
            for doc in retrieved_docs
        ])

        assembly_prompt = f"""Based on the query analysis:
{query_response.text}

And these retrieved documents:
{context_docs}

Organize the relevant information for answering the query. Include document citations [id] for each piece of information.

Organized Context:"""

        assembly_response = call_model(assembly_prompt, self.query_model, streaming)
        assembly_cost = calculate_cost(assembly_response.input_tokens, assembly_response.output_tokens, self.query_model)

        stage_results.append(StageResult(
            stage_name="context_assembly",
            stage_type=StageType.CONTEXT_ASSEMBLY,
            stage_order=3,
            input_text=assembly_prompt,
            output_text=assembly_response.text,
            input_tokens=assembly_response.input_tokens,
            output_tokens=assembly_response.output_tokens,
            cost=assembly_cost,
            latency_ms=assembly_response.latency_ms,
            model=get_model_id(self.query_model),
            success=assembly_response.success,
            time_to_first_token_ms=assembly_response.streaming_metrics.time_to_first_token_ms if assembly_response.streaming_metrics else None,
            tokens_per_second=assembly_response.streaming_metrics.tokens_per_second if assembly_response.streaming_metrics else None,
        ))

        total_cost += assembly_cost
        total_latency += assembly_response.latency_ms
        total_input_tokens += assembly_response.input_tokens
        total_output_tokens += assembly_response.output_tokens

        # Stage 4: Generation
        gen_model = self.generation_model or model
        generation_prompt = f"""Answer this question using the provided context. Include citations [id] for facts from the documents.

Question: {query}

Context:
{assembly_response.text}

Provide a comprehensive answer with proper citations:

Answer:"""

        gen_response = call_model(generation_prompt, gen_model, streaming)
        gen_cost = calculate_cost(gen_response.input_tokens, gen_response.output_tokens, gen_model)

        stage_results.append(StageResult(
            stage_name="generation",
            stage_type=StageType.GENERATION,
            stage_order=4,
            input_text=generation_prompt,
            output_text=gen_response.text,
            input_tokens=gen_response.input_tokens,
            output_tokens=gen_response.output_tokens,
            cost=gen_cost,
            latency_ms=gen_response.latency_ms,
            model=get_model_id(gen_model),
            success=gen_response.success,
            time_to_first_token_ms=gen_response.streaming_metrics.time_to_first_token_ms if gen_response.streaming_metrics else None,
            tokens_per_second=gen_response.streaming_metrics.tokens_per_second if gen_response.streaming_metrics else None,
        ))

        total_cost += gen_cost
        total_latency += gen_response.latency_ms
        total_input_tokens += gen_response.input_tokens
        total_output_tokens += gen_response.output_tokens

        final_output = gen_response.text

        # Stage 5: Verification (optional)
        if self.enable_verification:
            verify_prompt = f"""Review this response for citation accuracy:

Response:
{gen_response.text}

Available Documents:
{context_docs}

Check:
1. Are all citations [id] valid and accurate?
2. Are there any unsupported claims?
3. Are any important facts missing citations?

Verification Result (VERIFIED/NEEDS_CORRECTION):"""

            verify_response = call_model(verify_prompt, self.verification_model, streaming)
            verify_cost = calculate_cost(verify_response.input_tokens, verify_response.output_tokens, self.verification_model)

            stage_results.append(StageResult(
                stage_name="verification",
                stage_type=StageType.VERIFICATION,
                stage_order=5,
                input_text=verify_prompt,
                output_text=verify_response.text,
                input_tokens=verify_response.input_tokens,
                output_tokens=verify_response.output_tokens,
                cost=verify_cost,
                latency_ms=verify_response.latency_ms,
                model=get_model_id(self.verification_model),
                success=verify_response.success,
                time_to_first_token_ms=verify_response.streaming_metrics.time_to_first_token_ms if verify_response.streaming_metrics else None,
                tokens_per_second=verify_response.streaming_metrics.tokens_per_second if verify_response.streaming_metrics else None,
            ))

            total_cost += verify_cost
            total_latency += verify_response.latency_ms
            total_input_tokens += verify_response.input_tokens
            total_output_tokens += verify_response.output_tokens

        return PipelineResult(
            pipeline_name=self.name,
            stages=stage_results,
            final_output=final_output,
            total_cost=total_cost,
            total_latency_ms=total_latency,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            success=True,
        )
