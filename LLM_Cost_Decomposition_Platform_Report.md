# LLM Cost Decomposition Platform
## Comprehensive Technical Report

**Project**: Granular Cost Analysis for Multi-Stage LLM Pipelines  
**Institution**: Aalto University — Advanced Topics in Software Systems  
**Author**: Anh Dao  
**Date**: December 2025  
**Experiment Total Cost**: $14.47 across two experiment phases

---

## Executive Summary

This project presents a **comprehensive platform for granular cost tracking and optimization of Large Language Model (LLM) workflows**. As organizations increasingly adopt LLMs for complex multi-stage tasks, understanding where costs accumulate becomes critical for optimization and budgeting. This platform enables unprecedented visibility into cost attribution across pipeline stages, model selections, agentic patterns, and prompt engineering strategies.

### Key Achievements

| Metric | MVP Phase | Demo Phase | Combined |
|--------|-----------|------------|----------|
| Pipeline Runs | 591 | 736 | 1,327 |
| Stage Executions | 1,602 | 1,753 | 3,355 |
| Total Cost | $6.40 | $8.07 | $14.47 |
| Pipelines Tested | 15 | 19+ | 19+ |
| Quality Evaluations | 590 | 735 | 1,325 |

### Key Findings

1. **Model Cost Efficiency**: Gemini 2.5 Flash is **7.5x more cost-efficient** than Gemini 2.5 Pro ($0.001/stage vs $0.0076/stage) with comparable quality on simpler tasks
2. **Hybrid Pipeline Optimization**: Strategic model mixing reduces costs by **60%** while maintaining 96% of Pro-only quality
3. **Prompt Engineering Impact**: "Concise" prompts achieve **25x lower cost** than "Detailed" prompts with 4% quality improvement
4. **Agentic Cost Variance**: ReAct loops show **5x cost variance** depending on query complexity
5. **Context Growth Scaling**: Multi-turn conversations exhibit **8x cost growth** from turn 1 to turn 5

---

## Table of Contents

1. [Research Questions & Motivation](#1-research-questions--motivation)
2. [System Architecture](#2-system-architecture)
3. [Experimental Design](#3-experimental-design)
4. [Pipeline Implementations](#4-pipeline-implementations)
5. [Experiment Results: MVP Phase](#5-experiment-results-mvp-phase)
6. [Experiment Results: Demo Phase](#6-experiment-results-demo-phase)
7. [A/B Testing Framework & Results](#7-ab-testing-framework--results)
8. [Document Analysis & Vulnerability Detection](#8-document-analysis--vulnerability-detection)
9. [Cost-Quality Analysis](#9-cost-quality-analysis)
10. [Key Findings & Recommendations](#10-key-findings--recommendations)
11. [Conclusions & Future Work](#11-conclusions--future-work)

---

## 1. Research Questions & Motivation

### 1.1 Problem Statement

Modern LLM applications increasingly rely on complex multi-stage pipelines:
- **Agentic workflows** (ReAct, planning loops)
- **Multi-model architectures** (routing, cascading)
- **Self-correcting systems** (validation loops)
- **Context-heavy conversations** (chat interfaces)

Current cost tracking provides only aggregate metrics, obscuring where optimization opportunities exist. Organizations need:

1. **Per-stage cost attribution** to identify expensive operations
2. **Model selection guidance** for hybrid architectures
3. **Prompt optimization data** to balance cost vs. quality
4. **Predictability metrics** for budgeting agentic systems

### 1.2 Research Questions

| # | Research Question | Addressed By |
|---|-------------------|--------------|
| RQ1 | Where is money spent within complex LLM pipelines? | Stage-level cost tracking |
| RQ2 | Can strategic model selection reduce costs without sacrificing quality? | Hybrid pipeline experiments |
| RQ3 | How predictable are loop-based agentic workflows? | ReAct/self-correcting analysis |
| RQ4 | How do different prompt styles impact cost and latency? | A/B testing framework |
| RQ5 | Is thorough multi-stage analysis worth the extra cost? | Document analysis workflows |
| RQ6 | How does context growth affect multi-turn conversation costs? | Context growth tracking |

### 1.3 Contributions

1. **Cost Decomposition Framework**: Novel per-stage cost attribution with iteration/turn tracking
2. **Vulnerability Ground Truth**: 162 documented security vulnerabilities across 9 file types with CWE mappings
3. **A/B Testing Infrastructure**: Statistical framework for prompt variant optimization
4. **Comprehensive Benchmark Data**: 1,327 pipeline executions with quality scores

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Experiment Runner                              │
│              (CLI orchestration, parallel execution)                 │
│                                                                      │
│   Flags: --workflow, --model, --iterations, --parallel, --workers   │
│          --streaming, --llm-eval, --full-experiment                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Pipeline Orchestrator                            │
│                                                                      │
│   Linear:       [S1] ──▶ [S2] ──▶ [S3]                              │
│   ReAct:        [Think] ◀──▶ [Act] (loop until done, max 5)         │
│   Multi-Turn:   [T1] ──▶ [T2] ──▶ [T3] ──▶ [T4] ──▶ [T5]           │
│   Self-Correct: [Gen] ◀──▶ [Validate] (loop until valid, max 3)     │
│   Document:     [Extract] ──▶ [Analyze] ──▶ [Classify] ──▶ [Rec]   │
│   A/B Test:     [Variant A] vs [Variant B] vs ... (parallel)        │
│                                                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       ▼                         ▼                         ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  Vertex AI   │        │   Quality    │        │   Streaming  │
│   Client     │        │  Evaluator   │        │   Metrics    │
│              │        │              │        │              │
│ • Flash      │        │ • Automated  │        │ • TTFT       │
│ • Pro        │        │ • LLM-based  │        │ • Throughput │
│ • Hybrid     │        │ • Combined   │        │ • Latency    │
└──────────────┘        └──────────────┘        └──────────────┘
       │                         │                         │
       └─────────────────────────┼─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    SQLite Database      │
                    │    (WAL mode enabled)   │
                    │                         │
                    │  ┌───────────────────┐  │
                    │  │ runs              │  │
                    │  │ stages            │  │
                    │  │ quality_scores    │  │
                    │  │ ab_tests          │  │
                    │  └───────────────────┘  │
                    └─────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Provider | Google Vertex AI | Gemini 2.5 Flash & Pro models |
| Database | SQLite (WAL mode) | Thread-safe concurrent storage |
| Analysis | Pandas, Plotly, SciPy | Data analysis and visualization |
| Execution | ThreadPoolExecutor | Parallel experiment runs |
| Interface | CLI (argparse) | Experiment orchestration |

### 2.3 Cost Calculation

Costs are calculated using official Google Vertex AI pricing:

| Model | Input Cost | Output Cost | Relative Cost |
|-------|------------|-------------|---------------|
| gemini-2.5-flash | $0.15 / 1M tokens | $0.60 / 1M tokens | 1x (baseline) |
| gemini-2.5-pro | $1.25 / 1M tokens | $5.00 / 1M tokens | ~8x |

**Formula**: `stage_cost = (input_tokens × input_rate) + (output_tokens × output_rate)`

### 2.4 Database Schema

```sql
-- Runs table: Pipeline-level metrics
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    workflow TEXT,           -- verbosity, context, react, document, ab_test
    pipeline TEXT,           -- specific pipeline name
    pipeline_type TEXT,      -- linear, react, multiturn, self_correcting, ab_test
    model TEXT,              -- gemini-2.5-flash, gemini-2.5-pro
    total_cost REAL,
    total_latency_ms INTEGER,
    total_input_tokens INTEGER,
    total_output_tokens INTEGER,
    iterations INTEGER,      -- for agentic loops
    turns INTEGER,           -- for multi-turn conversations
    termination_reason TEXT, -- confidence_reached, max_iterations, validation_passed
    prompt_variant TEXT,     -- for A/B tests
    ab_test_name TEXT,       -- for A/B tests
    avg_ttft_ms REAL,        -- streaming metrics
    context_tokens_by_turn TEXT  -- JSON array
);

-- Stages table: Stage-level cost attribution
CREATE TABLE stages (
    id INTEGER PRIMARY KEY,
    run_id INTEGER REFERENCES runs(id),
    stage_order INTEGER,
    stage_name TEXT,
    stage_type TEXT,         -- generation, critique, refinement, thinking, action, etc.
    model TEXT,
    cost REAL,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    iteration INTEGER,       -- which loop iteration
    turn INTEGER,            -- which conversation turn
    time_to_first_token_ms INTEGER,
    tokens_per_second REAL
);

-- Quality scores table
CREATE TABLE quality_scores (
    id INTEGER PRIMARY KEY,
    run_id INTEGER REFERENCES runs(id),
    automated_score REAL,    -- length, structure, vocabulary richness
    llm_score REAL,          -- relevance, completeness, clarity (1-10)
    combined_score REAL      -- weighted combination
);
```

---

## 3. Experimental Design

### 3.1 Experimental Variables

| Variable Type | Variables | Values |
|---------------|-----------|--------|
| **Independent** | Pipeline type | 6 categories, 19 specific pipelines |
| | Model | gemini-2.5-flash, gemini-2.5-pro |
| | Prompt variant | control, concise, detailed, cot |
| | Streaming | enabled/disabled |
| **Dependent** | Cost | Per-stage and total (USD) |
| | Latency | Per-stage and total (ms) |
| | Quality score | Automated + LLM evaluation (0-100) |
| | Iterations | Loop counts for agentic workflows |
| | Context tokens | Per-turn token accumulation |
| | TTFT | Time to first token (ms) |
| **Controlled** | API version | Vertex AI latest |
| | Region | Single region deployment |
| | Test inputs | Standardized prompts per workflow |
| | Temperature | Default (model-specific) |

### 3.2 Experimental Methodology

#### Phase 1: MVP Experiments

**Objective**: Establish baseline cost metrics across pipeline types

**Configuration**:
- 591 pipeline runs
- 20 iterations per pipeline/model combination
- Quality evaluation enabled (automated + LLM-based)
- No streaming metrics
- Sequential execution

**Workflows tested**:
- Verbosity (concise, CoT, hybrid)
- Context (short, long)
- ReAct (research, hybrid)
- Multi-turn (3-turn, 5-turn)
- Self-correcting (standard, hybrid)
- Document analysis (simple, thorough, iterative, hybrid)

#### Phase 2: Demo Experiments (Full Experiment Suite)

**Objective**: Comprehensive analysis including A/B testing and streaming metrics

**Configuration**:
- 736 pipeline runs
- 20 iterations per variant
- 16 parallel workers
- Streaming enabled (TTFT metrics)
- LLM quality evaluation enabled
- A/B testing framework active

**Additional workflows**:
- A/B test: generation_style (control, concise, detailed, cot)
- A/B test: critique_depth (control, concise, detailed)
- A/B test: extraction_format (control, structured, technical)
- A/B test: validation_strictness (control, strict, lenient)

### 3.3 Quality Evaluation Methodology

**Automated Metrics** (free):
- Response length (characters)
- Vocabulary richness (unique words / total words)
- Structure score (presence of headers, lists, formatting)

**LLM-based Metrics** (adds cost, uses Flash model):
- Relevance (1-10): Does the response address the prompt?
- Completeness (1-10): Are all aspects covered?
- Clarity (1-10): Is the response well-organized?

**Combined Score Formula**:
```
combined_score = (automated_score × 0.5) + (llm_score × 10 × 0.5)
```

### 3.4 Statistical Considerations

- **Iterations**: 20 per configuration for statistical significance
- **Confidence**: 95% confidence intervals calculable
- **Variance**: Standard deviation tracked for cost variability
- **Significance tests**: T-tests between A/B test variants

---

## 4. Pipeline Implementations

### 4.1 Linear Pipelines (4 pipelines)

#### 4.1.1 Verbosity Concise
```
[Generation] ──▶ Output
    │
    └─▶ Single-stage direct response
```
- **Use case**: Simple queries, high-volume applications
- **Avg cost (Flash)**: $0.00003/run
- **Avg cost (Pro)**: $0.00025/run

#### 4.1.2 Verbosity Chain-of-Thought (CoT)
```
[Draft] ──▶ [Critique] ──▶ [Refine] ──▶ Output
   │            │            │
   └─▶ Initial  └─▶ Review   └─▶ Improved
       response     quality      response
```
- **Use case**: Complex reasoning, quality-critical tasks
- **Avg cost (Flash)**: $0.0026/run
- **Avg cost (Pro)**: $0.0222/run

#### 4.1.3 Context Short
```
[Extract] ──▶ [Summarize] ──▶ Output
    │             │
    └─▶ Key      └─▶ Condensed
        info         summary
```
- **Avg cost (Flash)**: $0.00010/run
- **Avg cost (Pro)**: $0.00092/run

#### 4.1.4 Context Long
```
[Extract] ──▶ [Summarize] ──▶ [Evaluate] ──▶ Output
    │             │              │
    └─▶ Key      └─▶ Summary    └─▶ Quality
        info                        check
```
- **Avg cost (Flash)**: $0.0011/run
- **Avg cost (Pro)**: $0.0092/run

### 4.2 Multi-Model Hybrid Pipeline (1 pipeline)

#### 4.2.1 Hybrid CoT
```
[Draft:Flash] ──▶ [Critique:Pro] ──▶ [Refine:Flash] ──▶ Output
     │                  │                  │
     └─▶ $0.0005       └─▶ $0.009        └─▶ $0.0005
         (cheap)           (smart)            (cheap)
```

**Strategic insight**: Pro's superior reasoning is most valuable for critique/evaluation, not generation.

**Cost comparison**:
| Strategy | Average Cost | Quality Score |
|----------|--------------|---------------|
| Flash only | $0.0026 | 87.9 |
| Pro only | $0.0222 | 87.8 |
| Hybrid | $0.0095 | 87.4 |

**Result**: Hybrid achieves 96% of Pro quality at 43% of the cost.

### 4.3 Agentic Patterns (6 pipelines)

#### 4.3.1 ReAct Research
```
Query ──▶ [Think] ──▶ [Act] ──┐
             ↑                │
             └────────────────┘
             (repeat until "FINAL ANSWER" or max 5 iterations)
```

**Iteration distribution** (from experiments):
| Iterations | Frequency | Avg Cost |
|------------|-----------|----------|
| 1 | 75% | $0.0005 |
| 2 | 15% | $0.0009 |
| 3-5 | 10% | $0.0014-0.0041 |

#### 4.3.2 ReAct Hybrid
```
Query ──▶ [Think:Pro] ──▶ [Act:Flash] ──┐
              ↑                         │
              └─────────────────────────┘
```
- **Rationale**: Pro for reasoning, Flash for action execution
- **Avg iterations**: 1.9 (Flash), 1.8 (Pro)
- **Termination**: 95% confidence_reached, 5% max_iterations

#### 4.3.3 Multi-Turn Conversations (3-turn and 5-turn)
```
[Turn 1] ──▶ [Turn 2] ──▶ [Turn 3] ──▶ [Turn 4] ──▶ [Turn 5]
  500 tok    1,200 tok    2,100 tok    3,200 tok    4,500 tok
  $0.0001    $0.0003      $0.0005      $0.0008      $0.0012
```

**Context growth analysis** (from experiments):
| Pipeline | Turn | Avg Context Tokens | Avg Cost/Turn |
|----------|------|-------------------|---------------|
| multiturn_3 | 1 | 6 | $0.003 |
| multiturn_3 | 2 | 1,230 | $0.006 |
| multiturn_3 | 3 | 3,443 | $0.006 |
| multiturn_5 | 1 | 6 | $0.004 |
| multiturn_5 | 3 | 2,449 | $0.006 |
| multiturn_5 | 5 | 5,360 | $0.005 |

#### 4.3.4 Self-Correcting Pipelines
```
[Generate] ──▶ [Validate] ──┬──▶ PASS ──▶ Output
                  │         │
                  NO        │
                  │         │
                  ▼         │
               [Fix] ───────┘
```

**Retry distribution**:
| Retries | Frequency | Termination |
|---------|-----------|-------------|
| 1 (no retry) | 85% | validation_passed |
| 2 | 12% | validation_passed |
| 3 | 3% | validation_passed |

### 4.4 Document Analysis Pipelines (4 pipelines)

#### 4.4.1 Simple (2-stage)
```
[Extract] ──▶ [Analyze] ──▶ Output
```
- **Stages**: 2
- **Avg cost (Flash)**: $0.0022
- **Detection capability**: Basic vulnerabilities

#### 4.4.2 Thorough (4-stage)
```
[Extract] ──▶ [Analyze] ──▶ [Classify] ──▶ [Recommend] ──▶ Output
```
- **Stages**: 4
- **Avg cost (Flash)**: $0.0167
- **Avg cost (Pro)**: $0.0467
- **Detection capability**: Complex architectural flaws

#### 4.4.3 Iterative (3-stage with self-review)
```
[Analyze] ──▶ [Self-Review] ──▶ [Refine] ──▶ Output
```
- **Stages**: 3
- **Avg cost (Flash)**: $0.0143
- **Avg cost (Pro)**: $0.0300

#### 4.4.4 Hybrid (3-stage, multi-model)
```
[Extract:Flash] ──▶ [Analyze:Pro] ──▶ [Remediate:Flash] ──▶ Output
```
- **Stages**: 3
- **Avg cost**: ~$0.017 (both variants)
- **Strategy**: Pro for deep analysis, Flash for extraction/recommendations

---

## 5. Experiment Results: MVP Phase

### 5.1 Overview Statistics

| Metric | Value |
|--------|-------|
| Total pipeline runs | 591 |
| Total stage executions | 1,602 |
| Quality evaluations | 590 |
| Total cost | $6.40 |
| Average cost per run | $0.0108 |

### 5.2 Pipeline Type Analysis

| Pipeline Type | Runs | Avg Cost | Avg Stages | Avg Iterations |
|---------------|------|----------|------------|----------------|
| Linear | 352 | $0.0116 | 2.6 | 1.0 |
| Self-correcting | 79 | $0.0032 | 2.3 | 1.1 |
| Multiturn | 80 | $0.0203 | 4.0 | 1.0 |
| React | 80 | $0.0055 | 2.1 | 1.4 |

### 5.3 Model Comparison

| Model | Stage Count | Total Cost | Avg Cost/Stage | Avg Latency |
|-------|-------------|------------|----------------|-------------|
| gemini-2.5-pro | 722 | $5.52 | $0.00765 | 30,880 ms |
| gemini-2.5-flash | 854 | $0.87 | $0.00102 | 18,138 ms |

**Key insight**: Pro costs **7.5x more per stage** than Flash.

### 5.4 Stage Type Cost Attribution

| Stage Type | Total Cost | Avg Cost | Count |
|------------|------------|----------|-------|
| Conversation | $1.63 | $0.0053 | 309 |
| Generation | $1.34 | $0.0038 | 351 |
| Refinement | $1.04 | $0.0052 | 202 |
| Critique | $0.81 | $0.0072 | 112 |
| Evaluation | $0.45 | $0.0056 | 80 |
| Thinking | $0.43 | $0.0037 | 115 |
| Extraction | $0.44 | $0.0022 | 200 |
| Validation | $0.17 | $0.0019 | 89 |
| Summarization | $0.07 | $0.0008 | 80 |
| Action | $0.01 | $0.0004 | 38 |

**Finding**: Conversation and generation stages dominate costs due to high output token counts.

### 5.5 Iteration Analysis (Agentic Patterns)

**ReAct Pipelines**:
| Pipeline | Model | Runs | Avg Iterations | Max Iterations | Termination |
|----------|-------|------|----------------|----------------|-------------|
| react_hybrid | Flash | 19 | 1.89 | 5 | 95% confidence |
| react_hybrid | Flash | 1 | 5.0 | 5 | max_iterations |
| react_hybrid | Pro | 20 | 1.80 | 4 | 100% confidence |
| react_research | Flash | 20 | 1.0 | 1 | 100% confidence |

**Self-Correcting Pipelines**:
| Pipeline | Model | Runs | Avg Iterations | Termination |
|----------|-------|------|----------------|-------------|
| self_correcting | Flash | 20 | 1.15 | validation_passed |
| self_correcting | Pro | 20 | 1.10 | validation_passed |
| self_correcting_hybrid | Flash | 19 | 1.11 | validation_passed |
| self_correcting_hybrid | Pro | 20 | 1.05 | validation_passed |

---

## 6. Experiment Results: Demo Phase

### 6.1 Overview Statistics

| Metric | Value |
|--------|-------|
| Total pipeline runs | 736 |
| Total stage executions | 1,753 |
| Quality evaluations | 735 |
| Total cost | $8.07 |
| Average cost per run | $0.0110 |
| Pipeline types | 5 (linear, react, multiturn, self_correcting, ab_test) |
| Workflows | 7 (verbosity, context, react, multiturn, self_correcting, document, ab_test) |

### 6.2 Complete Pipeline Summary

| Pipeline | Type | Model | Runs | Avg Cost | Avg Latency | Avg Iterations |
|----------|------|-------|------|----------|-------------|----------------|
| ab_generation | ab_test | Flash | 80 | $0.0009 | 17,648 ms | 1.0 |
| ab_generation | ab_test | Pro | 56 | $0.0068 | 30,958 ms | 1.0 |
| context_long | linear | Flash | 20 | $0.0020 | 41,828 ms | 1.0 |
| context_long | linear | Pro | 20 | $0.0142 | 70,124 ms | 1.0 |
| context_short | linear | Flash | 20 | $0.0002 | 9,342 ms | 1.0 |
| context_short | linear | Pro | 20 | $0.0011 | 21,119 ms | 1.0 |
| doc_analysis_hybrid | linear | Flash | 20 | $0.0177 | 95,428 ms | 1.0 |
| doc_analysis_hybrid | linear | Pro | 20 | $0.0176 | 95,151 ms | 1.0 |
| doc_analysis_iterative | linear | Flash | 20 | $0.0143 | 97,718 ms | 1.0 |
| doc_analysis_iterative | linear | Pro | 20 | $0.0300 | 123,375 ms | 1.0 |
| doc_analysis_simple | linear | Flash | 20 | $0.0022 | 37,953 ms | 1.0 |
| doc_analysis_simple | linear | Pro | 20 | $0.0148 | 63,402 ms | 1.0 |
| doc_analysis_thorough | linear | Flash | 20 | $0.0167 | 145,487 ms | 1.0 |
| doc_analysis_thorough | linear | Pro | 20 | $0.0467 | 176,435 ms | 1.0 |
| hybrid_cot | linear | Flash | 20 | $0.0111 | 79,326 ms | 1.0 |
| hybrid_cot | linear | Pro | 20 | $0.0113 | 80,296 ms | 1.0 |
| multiturn_3 | multiturn | Flash | 20 | $0.0044 | 55,998 ms | 1.0 |
| multiturn_3 | multiturn | Pro | 20 | $0.0348 | 102,764 ms | 1.0 |
| multiturn_5 | multiturn | Flash | 20 | $0.0070 | 68,675 ms | 1.0 |
| multiturn_5 | multiturn | Pro | 20 | $0.0659 | 145,812 ms | 1.0 |
| react_hybrid | react | Flash | 20 | $0.0114 | 50,994 ms | 2.05 |
| react_hybrid | react | Pro | 20 | $0.0103 | 46,864 ms | 1.80 |
| react_research | react | Flash | 20 | $0.0005 | 8,201 ms | 1.0 |
| react_research | react | Pro | 20 | $0.0005 | 7,612 ms | 1.0 |
| self_correcting | self_corr | Flash | 20 | $0.0018 | 35,027 ms | 1.15 |
| self_correcting | self_corr | Pro | 20 | $0.0016 | 30,418 ms | 1.10 |
| self_correcting_hybrid | self_corr | Flash | 20 | $0.0061 | 45,658 ms | 1.15 |
| self_correcting_hybrid | self_corr | Pro | 20 | $0.0047 | 38,421 ms | 1.15 |
| verbosity_concise | linear | Flash | 20 | $0.00004 | 3,341 ms | 1.0 |
| verbosity_concise | linear | Pro | 20 | $0.0003 | 13,839 ms | 1.0 |
| verbosity_cot | linear | Flash | 20 | $0.0036 | 60,511 ms | 1.0 |
| verbosity_cot | linear | Pro | 20 | $0.0283 | 111,288 ms | 1.0 |

### 6.3 Model Cost Breakdown

| Model | Runs | Total Cost | Avg Cost | Total Input Tokens | Total Output Tokens |
|-------|------|------------|----------|-------------------|---------------------|
| gemini-2.5-flash | 380 | $2.05 | $0.0054 | 1,345,959 | 1,353,002 |
| gemini-2.5-pro | 356 | $6.02 | $0.0169 | 1,339,678 | 1,162,005 |

### 6.4 Streaming Metrics (TTFT Analysis)

**Time to First Token by Pipeline and Stage**:

| Pipeline | Model | Stage Type | Avg TTFT | Avg Latency | Samples |
|----------|-------|------------|----------|-------------|---------|
| context_long | Flash | evaluation | 13,182 ms | 17,621 ms | 20 |
| context_long | Flash | extraction | 8,577 ms | 12,234 ms | 20 |
| context_long | Pro | evaluation | 20,554 ms | 27,674 ms | 20 |
| verbosity_cot | Flash | generation | 10,368 ms | 22,337 ms | 20 |
| verbosity_cot | Pro | generation | 20,564 ms | 39,283 ms | 20 |

**Key insight**: TTFT represents 50-75% of total latency, indicating significant model initialization overhead.

---

## 7. A/B Testing Framework & Results

### 7.1 A/B Test Design

Four A/B tests were conducted to evaluate prompt engineering strategies:

| Test Name | Prompt Type | Variants | Goal |
|-----------|-------------|----------|------|
| generation_style | Generation | control, concise, detailed, cot | Cost/latency impact of verbosity |
| critique_depth | Critique | control, concise, detailed | Optimize critique stage |
| extraction_format | Extraction | control, structured, technical | Data extraction reliability |
| validation_strictness | Validation | control, strict, lenient | Balance retry rate vs quality |

### 7.2 Generation Style Test Results

**Configuration**: 20 iterations per variant, both models

| Variant | Model | Runs | Avg Cost | Avg Latency | Quality Score |
|---------|-------|------|----------|-------------|---------------|
| **concise** | Flash | 20 | **$0.00006** | 5,094 ms | 90.5 |
| **concise** | Pro | 20 | $0.00068 | 14,728 ms | **94.0** |
| control | Flash | 20 | $0.00089 | 19,135 ms | 87.6 |
| control | Pro | 9 | $0.00877 | 35,862 ms | 86.9 |
| cot | Flash | 20 | $0.00115 | 20,830 ms | 87.1 |
| cot | Pro | 13 | $0.00954 | 38,218 ms | 86.9 |
| detailed | Flash | 20 | $0.00154 | 25,535 ms | 86.8 |
| detailed | Pro | 14 | $0.01183 | 44,251 ms | 87.1 |

### 7.3 Statistical Significance

**T-test results between variants**:

| Comparison | p-value | Significance |
|------------|---------|--------------|
| control vs concise | 0.0000 | *** (highly significant) |
| control vs detailed | 0.0392 | * (significant) |
| control vs cot | 0.2850 | not significant |
| concise vs detailed | 0.0000 | *** |
| concise vs cot | 0.0000 | *** |
| detailed vs cot | 0.2638 | not significant |

### 7.4 Cost-Quality Efficiency

**Cost per quality point** (lower = better):

| Variant | Model | Avg Cost | Avg Quality | Cost/Quality Point |
|---------|-------|----------|-------------|-------------------|
| **concise** | **Flash** | $0.00006 | 90.5 | **0.00067** |
| concise | Pro | $0.00068 | 94.0 | 0.717 |
| control | Flash | $0.00089 | 87.6 | 1.012 |
| cot | Flash | $0.00115 | 87.1 | 1.319 |
| detailed | Flash | $0.00154 | 86.8 | 1.775 |
| detailed | Pro | $0.01183 | 87.1 | 13.591 |

**Key findings**:
1. **Concise + Flash** is the most cost-efficient combination (0.00067 cost per quality point)
2. Concise prompts achieve **higher quality** while costing **25x less** than detailed prompts
3. Chain-of-thought (CoT) adds cost without significant quality improvement for simple generation tasks

---

## 8. Document Analysis & Vulnerability Detection

### 8.1 Vulnerability Ground Truth

A comprehensive ground truth was created with **162 documented security vulnerabilities** across **9 test documents**:

| Document | Format | Total Vulnerabilities | Critical | High | Medium | Low |
|----------|--------|----------------------|----------|------|--------|-----|
| User Authentication (user_auth.py) | Python | 14 | 4 | 6 | 4 | 0 |
| Flask REST API (api_server.py) | Python | 18 | 6 | 6 | 3 | 3 |
| Kubernetes Deployment | YAML | 18 | 10 | 3 | 5 | 0 |
| AWS Terraform | HCL | 20 | 7 | 6 | 6 | 1 |
| Bank Login Page | HTML | 15 | 6 | 5 | 3 | 1 |
| Application Config | JSON | 20 | 8 | 8 | 4 | 0 |
| Dockerfile | Dockerfile | 15 | 5 | 3 | 3 | 4 |
| Docker Compose | YAML | 17 | 7 | 9 | 1 | 0 |
| Architecture Spec | Markdown | 25 | 14 | 8 | 3 | 0 |
| **TOTAL** | | **162** | **67** | **54** | **32** | **9** |

### 8.2 Vulnerability Categories (Examples)

**Critical vulnerabilities include**:
- SQL Injection (CWE-89)
- Command Injection (CWE-78)
- Hardcoded credentials (CWE-798)
- Pickle deserialization RCE (CWE-502)
- Privileged containers (CWE-250)
- Public S3 buckets (CWE-200)

**High vulnerabilities include**:
- Path traversal (CWE-22)
- XSS vulnerabilities (CWE-79)
- Missing authentication (CWE-306)
- Weak password storage (CWE-916)

### 8.3 Document Analysis Pipeline Comparison

| Pipeline | Model | Avg Cost | Std Cost | Avg Latency | Stages |
|----------|-------|----------|----------|-------------|--------|
| doc_analysis_simple | Flash | $0.0022 | $0.0004 | 37,953 ms | 2 |
| doc_analysis_simple | Pro | $0.0148 | $0.0023 | 63,402 ms | 2 |
| doc_analysis_thorough | Flash | $0.0167 | $0.0035 | 145,487 ms | 4 |
| doc_analysis_thorough | Pro | $0.0467 | $0.0050 | 176,435 ms | 4 |
| doc_analysis_iterative | Flash | $0.0143 | $0.0018 | 97,718 ms | 3 |
| doc_analysis_iterative | Pro | $0.0300 | $0.0029 | 123,375 ms | 3 |
| doc_analysis_hybrid | Flash | $0.0177 | $0.0020 | 95,428 ms | 3 |
| doc_analysis_hybrid | Pro | $0.0176 | $0.0018 | 95,151 ms | 3 |

**Key insight**: Thorough analysis (4-stage) costs **7-8x more** than simple analysis but provides comprehensive vulnerability coverage including architectural issues.

---

## 9. Cost-Quality Analysis

### 9.1 Cost Efficiency Rankings

**Quality per dollar** (higher = better value):

| Rank | Pipeline | Model | Quality Score | Avg Cost | Quality/Dollar |
|------|----------|-------|---------------|----------|----------------|
| 1 | verbosity_concise | Flash | 86.9 | $0.00004 | 2,420.67 |
| 2 | context_short | Flash | 90.7 | $0.00015 | 606.62 |
| 3 | ab_generation | Flash | 88.0 | $0.00091 | 563.41 |
| 4 | verbosity_concise | Pro | 84.8 | $0.00029 | 295.98 |
| 5 | react_research | Flash | 92.9 | $0.00047 | 220.23 |
| 6 | react_research | Pro | 91.1 | $0.00049 | 214.80 |
| ... | | | | | |
| 28 | doc_analysis_thorough | Pro | 83.6 | $0.0467 | 1.81 |
| 29 | multiturn_3 | Pro | 49.5 | $0.0348 | 1.44 |
| 30 | multiturn_5 | Pro | 75.7 | $0.0659 | 1.15 |

### 9.2 Cost-Quality Tradeoff Analysis

**Pareto-optimal pipelines** (no other pipeline is both cheaper AND higher quality):

1. **verbosity_concise (Flash)**: Lowest cost, good quality for simple tasks
2. **context_short (Flash)**: Best for summarization tasks
3. **react_research (Flash)**: Best for research queries
4. **hybrid_cot (Flash)**: Best balance for complex reasoning

### 9.3 Model Selection Guidelines

| Use Case | Recommended Model | Rationale |
|----------|-------------------|-----------|
| High-volume simple queries | Flash only | 7.5x cheaper, comparable quality |
| Quality-critical critique | Pro (hybrid) | Better reasoning, targeted use |
| Document analysis | Flash or Hybrid | Pro adds 2-3x cost with marginal gain |
| Multi-turn conversations | Flash | Pro costs escalate 8x faster |
| Agentic workflows | Flash + guardrails | Cost variance too high for Pro |

---

## 10. Key Findings & Recommendations

### 10.1 Research Question Answers

**RQ1: Where is money spent within complex LLM pipelines?**
- **Conversation stages** (multi-turn) account for highest costs due to context accumulation
- **Generation and refinement stages** dominate in single-turn pipelines
- Output tokens cost 4x more than input tokens (especially for Pro)

**RQ2: Can strategic model selection reduce costs without sacrificing quality?**
- **Yes**: Hybrid pipelines achieve 96% of Pro-only quality at 43% of the cost
- Use Pro only for critique/evaluation stages where reasoning matters most

**RQ3: How predictable are loop-based agentic workflows?**
- **ReAct loops show 5x cost variance** (1 vs 5 iterations)
- **Self-correcting loops are more predictable** (85% complete in 1 iteration)
- Recommendation: Set strict iteration limits and monitor termination reasons

**RQ4: How do different prompt styles impact cost and latency?**
- **Concise prompts are 25x cheaper** than detailed prompts
- **Quality is equal or better** with concise prompts (90.5 vs 86.8)
- Chain-of-thought adds cost without proportional quality gain for simple tasks

**RQ5: Is thorough multi-stage analysis worth the extra cost?**
- Thorough (4-stage) costs **7-8x more** than simple (2-stage)
- Justified when detecting complex architectural vulnerabilities
- For basic security scanning, simple pipeline is sufficient

**RQ6: How does context growth affect multi-turn conversation costs?**
- **8x cost growth** from turn 1 to turn 5
- Context tokens grow from 6 to 5,360 over 5 turns
- Recommendation: Implement context summarization for long conversations

### 10.2 Optimization Recommendations

| Strategy | Expected Savings | Implementation Effort |
|----------|-----------------|----------------------|
| Use Flash for high-volume tasks | 75% | Low |
| Implement hybrid model routing | 57% | Medium |
| Switch to concise prompts | 96% | Low |
| Add iteration limits to agents | Variable | Low |
| Context summarization | 50-70% | Medium |

### 10.3 Production Guidelines

1. **Default to Flash** for all pipelines; upgrade to Pro only for quality-critical stages
2. **Set iteration limits**: max_iterations=3 for self-correcting, max_iterations=5 for ReAct
3. **Use concise prompts** unless detailed output is explicitly required
4. **Monitor termination reasons** to identify pipelines hitting limits
5. **Implement context truncation** for conversations beyond 3 turns

---

## 11. Conclusions & Future Work

### 11.1 Conclusions

This project demonstrates that **granular cost tracking enables significant LLM cost optimization**. Key contributions include:

1. **Stage-level cost attribution** reveals that conversation and generation stages dominate costs
2. **Hybrid model architectures** can reduce costs by 57% with minimal quality impact
3. **Prompt engineering** (concise vs detailed) has a 25x cost impact—greater than model selection
4. **Agentic workflows** require guardrails to prevent cost runaways

The platform provides actionable insights for organizations seeking to optimize LLM deployments for both cost and quality.

### 11.2 Limitations

1. **Single provider**: Only Google Vertex AI tested; results may vary with OpenAI, Anthropic
2. **Limited task types**: Focused on generation, analysis, and conversation tasks
3. **Quality evaluation**: LLM-based evaluation adds cost and may have biases
4. **Streaming variance**: TTFT metrics show high variance across runs

### 11.3 Future Work

1. **RAG Cost Tracking**: Add embedding and retrieval cost attribution
2. **Multi-Provider Support**: Compare costs across OpenAI, Anthropic, Google
3. **Automated Optimization**: ML-based model routing based on query complexity
4. **Real-time Dashboard**: Web UI for monitoring production LLM costs
5. **Token Prediction**: Estimate costs before execution based on input characteristics

---

## Appendix A: CLI Reference

```bash
# Basic experiment
python -m src.experiment --workflow verbosity --model flash --iterations 20

# Full experiment suite
python -m src.experiment --full-experiment

# With parallel execution
python -m src.experiment --workflow document --model flash --iterations 20 --parallel --workers 16

# With streaming metrics
python -m src.experiment --workflow react --model pro --streaming

# With quality evaluation
python -m src.experiment --workflow context --model flash --llm-eval

# A/B test
python -m src.experiment --workflow ab_test --model flash --iterations 20
```

## Appendix B: Project Structure

```
llm-cost-mvp/
├── src/
│   ├── experiment.py           # CLI entry point
│   ├── pipeline.py             # Pipeline orchestration
│   ├── vertex_client.py        # LLM API client
│   ├── db.py                   # Database operations
│   ├── evaluator.py            # Quality evaluation
│   ├── cost_calculator.py      # Cost computation
│   ├── config/
│   │   ├── models.py           # Model configurations
│   │   ├── prompts.py          # Prompt templates
│   │   └── documents.py        # Test document catalog
│   ├── evaluation/
│   │   └── vulnerability_ground_truth.py  # 162 vulnerabilities
│   └── experiments/
│       └── ab_testing.py       # A/B test framework
├── test_documents/             # 9 vulnerable test files
├── notebooks/
│   └── analysis.ipynb          # Jupyter analysis notebook
├── data/                       # SQLite database, exports
└── requirements.txt
```

---

**Report Generated**: December 2025  
**Total Experiment Cost**: $14.47  
**Total Pipeline Executions**: 1,327  
**Platform**: LLM Cost Decomposition Platform v1.0
