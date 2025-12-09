"""
Pipeline registry and pre-defined pipeline instances.

Contains:
- All 16+ pipeline instances
- PIPELINES dict for lookup
- get_pipeline() and list_pipelines() functions
"""

from .base import StageType, PipelineStage, Pipeline
from .agentic import ReActPipeline, MultiTurnPipeline, SelfCorrectingPipeline
from .rag import RAGPipeline


# =============================================================================
# Pre-defined Pipelines
# =============================================================================

# --- Standard Pipelines ---

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

# --- RAG Pipelines ---

RAG_BASIC_PIPELINE = RAGPipeline(
    name="rag_basic",
    description="Basic RAG: 5 docs, no verification",
    retrieval_k=5,
    enable_verification=False,
    query_model="flash",
    generation_model="flash",
)

RAG_VERIFIED_PIPELINE = RAGPipeline(
    name="rag_verified",
    description="Verified RAG: 10 docs with citation verification",
    retrieval_k=10,
    enable_verification=True,
    query_model="flash",
    generation_model="flash",
)

RAG_HYBRID_PIPELINE = RAGPipeline(
    name="rag_hybrid",
    description="Hybrid RAG: Flash retrieval, Pro generation",
    retrieval_k=10,
    enable_verification=True,
    query_model="flash",
    generation_model="pro",
)

# --- Document Analysis Pipelines ---

DOC_ANALYSIS_SIMPLE_PIPELINE = Pipeline(
    name="doc_analysis_simple",
    description="Simple 2-stage document analysis: Extract key info -> Identify issues",
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
    description="Thorough 4-stage analysis: Extract -> Analyze -> Classify -> Recommend",
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
    description="Iterative analysis with self-review: Analyze -> Review -> Refine",
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
    # RAG
    "rag_basic": RAG_BASIC_PIPELINE,
    "rag_verified": RAG_VERIFIED_PIPELINE,
    "rag_hybrid": RAG_HYBRID_PIPELINE,
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
        elif isinstance(p, RAGPipeline):
            result.append({
                "name": p.name,
                "description": p.description,
                "type": "rag",
                "retrieval_k": p.retrieval_k,
                "stages": ["query_understanding", "retrieval", "context_assembly", "generation"]
                         + (["verification"] if p.enable_verification else []),
                "multi_model": p.query_model != p.generation_model,
            })
    return result
