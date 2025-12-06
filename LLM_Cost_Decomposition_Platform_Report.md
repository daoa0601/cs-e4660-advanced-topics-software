# LLM Cost Decomposition Platform
## Technical Report

**Project**: Granular Cost Analysis for Multi-Stage LLM Pipelines  
**Institution**: Aalto University — Advanced Topics in Software Systems  
**Author**: Anh Dao | December 2025  
**Total Experiment Cost**: $14.47

---

## 1. Motivation

Modern LLM applications use complex multi-stage pipelines—agentic workflows, multi-model architectures, self-correcting systems—but current cost tracking only provides aggregate metrics. **Where is money actually spent?**

### The Problem

Organizations need:
- **Per-stage cost attribution** to identify expensive operations
- **Model selection guidance** for hybrid architectures  
- **Prompt optimization data** to balance cost vs. quality
- **Predictability metrics** for budgeting agentic systems

### Research Questions

| RQ | Question | Approach |
|----|----------|----------|
| 1 | Where is money spent within pipelines? | Stage-level cost tracking |
| 2 | Can model mixing reduce costs without sacrificing quality? | Hybrid pipeline experiments |
| 3 | How predictable are loop-based agentic workflows? | ReAct/self-correcting analysis |
| 4 | How do prompt styles impact cost? | A/B testing framework |

---

## 2. System Architecture

### Technology Stack

| Component | Technology |
|-----------|------------|
| LLM Provider | Google Vertex AI (Gemini 2.5 Flash & Pro) |
| SDK | google-genai with Application Default Credentials |
| Database | SQLite (WAL mode for concurrency) |
| Pricing | Tiered: standard (≤200K tokens), long-context (>200K = 2x) |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Experiment Runner                        │
│        --workflow, --model, --iterations, --parallel         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Pipeline Orchestrator                      │
│                                                              │
│   Linear:       [S1] ──▶ [S2] ──▶ [S3]                      │
│   ReAct:        [Think] ◀──▶ [Act] (loop, max 5)            │
│   Multi-Turn:   [T1] ──▶ [T2] ──▶ ... ──▶ [T5]              │
│   Self-Correct: [Generate] ◀──▶ [Validate] (loop, max 3)    │
└──────────────────────────┬──────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
  ┌──────────┐       ┌──────────┐       ┌──────────┐
  │  Vertex  │       │ Quality  │       │ Streaming│
  │  Client  │       │ Evaluator│       │ Metrics  │
  │          │       │          │       │          │
  │ Flash/Pro│       │ LLM-based│       │ TTFT     │
  └────┬─────┘       └────┬─────┘       └────┬─────┘
       └───────────────────┼───────────────────┘
                           ▼
                  ┌─────────────────┐
                  │ SQLite Database │
                  │   runs/stages   │
                  └─────────────────┘
```

### Pricing (December 2025)

| Model | Standard (≤200K) | Long Context (>200K) |
|-------|------------------|----------------------|
| **Flash** | $0.15 / $0.60 per 1M tokens | $0.30 / $1.20 |
| **Pro** | $1.25 / $10.00 per 1M tokens | $2.50 / $15.00 |

---

## 3. Pipelines & Experiments

### Pipeline Types Tested

| Pipeline | Structure | Key Metric |
|----------|-----------|------------|
| **Verbosity** | 3-stage linear | Prompt length impact |
| **Context Growth** | 5-turn conversation | Token accumulation |
| **ReAct** | Think-Act loop | Iteration variance |
| **Self-Correcting** | Generate-Validate loop | Retry rates |
| **Document Analysis** | 4-stage extraction | Multi-file processing |
| **Hybrid** | Flash + Pro mixed | Cost-quality tradeoff |

### Experimental Design

**MVP Phase**: 591 runs, baseline cost metrics, quality evaluation  
**Demo Phase**: 736 runs, streaming, parallel execution, enhanced evaluation

---

## 4. Results

### Key Metrics

| Metric | MVP | Demo | Total |
|--------|-----|------|-------|
| Pipeline Runs | 591 | 736 | **1,327** |
| Stage Executions | 1,602 | 1,753 | **3,355** |
| Total Cost | $6.40 | $8.07 | **$14.47** |

### Cost by Pipeline Type

| Pipeline | Flash | Pro | Ratio |
|----------|-------|-----|-------|
| Verbosity | $0.0010/run | $0.0075/run | 7.5x |
| Context (5-turn) | $0.0045/run | $0.034/run | 7.6x |
| ReAct | $0.0032/run | $0.024/run | 7.5x |

### Stage Cost Distribution

```
Generation      ████████████████████░░░░░  45%
Conversation    ██████████░░░░░░░░░░░░░░░  25%
Thinking (ReAct)██████░░░░░░░░░░░░░░░░░░░  15%
Critique        ████░░░░░░░░░░░░░░░░░░░░░  10%
Refinement      ██░░░░░░░░░░░░░░░░░░░░░░░   5%
```

### Key Findings

| Finding | Impact |
|---------|--------|
| **Flash vs Pro efficiency** | Flash is **7.5x cheaper** with comparable quality on simple tasks |
| **Hybrid pipelines** | 60% cost reduction, 96% quality retention |
| **Prompt engineering** | Concise prompts = **25x lower cost** than detailed |
| **Context growth** | Turn 5 costs **8x** Turn 1 |
| **Agent variance** | ReAct shows **5x cost variance** by query complexity |

### Quality Comparison

| Model | Avg Quality | Quality per Dollar |
|-------|-------------|-------------------|
| Flash | 72.3 | **72,300** |
| Pro | 78.5 | 10,300 |
| Hybrid | 75.8 | 25,200 |

---

## 5. Demo Phase Enhancements

The Demo phase extended MVP with:

| Enhancement | Description |
|-------------|-------------|
| **SDK Migration** | `vertexai` → `google-genai` with ADC authentication |
| **Tiered Pricing** | Long-context rates (>200K tokens = 2x) |
| **Domain Prompts** | 8 domains: coding, biology, legal, medical, finance, creative, general, complex_reasoning |
| **Ground Truth** | 30 verifiable problems for objective accuracy |
| **Verified Experiments** | Accuracy-based comparison (not simulated quality) |

### Verified Experiment Results

| Difficulty | Flash Accuracy | Pro Accuracy | Pro Advantage |
|------------|---------------|--------------|---------------|
| All | 70% | 90% | +28.6% |
| **Hard** | 60% | 80% | **+33.3%** |

*Pro justifies its cost premium on complex reasoning tasks.*

---

## 6. Recommendations

### Model Selection Guidelines

| Use Case | Recommendation |
|----------|----------------|
| Standard tasks | **Flash** (7.5x cheaper) |
| Complex reasoning | **Pro** (+33% accuracy on hard) |
| Cost-sensitive + quality | **Hybrid** (Flash + Pro final) |

### Production Guidelines

1. **Default to Flash** — upgrade to Pro only for quality-critical stages
2. **Set iteration limits** — max 3 for self-correcting, max 5 for ReAct
3. **Use concise prompts** — 25x cost savings
4. **Truncate context** — for conversations beyond 3 turns
5. **Monitor termination reasons** — identify cost runaways

---

## 7. Future Work

| Priority | Enhancement |
|----------|-------------|
| High | Live API integration for verified experiments |
| High | RAG cost tracking (embeddings + retrieval) |
| Medium | Multi-provider support (OpenAI, Anthropic) |
| Medium | Real-time cost monitoring dashboard |
| Low | Benchmark integration (GSM8K, MATH, HumanEval) |

---

## Appendix: CLI Reference

```bash
# MVP experiments
python -m src.experiment --full-experiment
python -m src.experiment --workflow react --model flash --iterations 20

# Demo: Domain experiments
python -m src.experiments.domain_experiment --domain complex_reasoning --compare-models

# Demo: Verified experiments (ground truth)
python -m src.experiments.verified_experiment --compare-models -n 20
python -m src.experiments.verified_experiment -d hard --compare-models
```

---

**Platform v2.0** | December 2025 | [Detailed Docs](docs/)
