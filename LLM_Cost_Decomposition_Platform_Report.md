# LLM Cost Decomposition Platform
## Technical Report

**Version**: 3.0  
**Project**: Granular Cost Analysis for Multi-Stage LLM Pipelines  
**Institution**: Aalto University — Advanced Topics in Software Systems  
**Author**: Anh Dao | December 2025  
**Total Experiment Cost**: $16.72

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
┌─────────────────────────────────────────────────────────────────┐
│                     Experiment Runner (CLI)                      │
│       --workflow, --model, --iterations, --parallel              │
│                      src/experiment/cli.py                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                         │
│                       src/pipeline/                              │
│                                                                  │
│   Linear:       [S1] ──▶ [S2] ──▶ [S3]                          │
│   ReAct:        [Think] ◀──▶ [Act] (loop, max 5)                │
│   Multi-Turn:   [T1] ──▶ [T2] ──▶ ... ──▶ [T5]                  │
│   Self-Correct: [Generate] ◀──▶ [Validate] (loop, max 3)        │
│   RAG:          [Query] ──▶ [Retrieve] ──▶ [Generate] ──▶ [Verify]│
└──────────────────────────────┬──────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
      ┌──────────┐       ┌──────────┐       ┌──────────┐
      │ GenAI    │       │ Quality  │       │ Streaming│
      │ Client   │       │ Evaluator│       │ Metrics  │
      │          │       │          │       │          │
      │ Flash/Pro│       │ LLM-based│       │ TTFT     │
      └────┬─────┘       └────┬─────┘       └────┬─────┘
           └──────────────────┼──────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
   ┌────────────────────┐         ┌────────────────────┐
   │  SQLite Database   │         │   Visualization    │
   │    src/db/         │         │ src/visualization/ │
   └────────────────────┘         └────────────────────┘
```

### v3.0 Modular Architecture

The codebase uses a modular package structure:

| Package | Purpose | Key Components |
|---------|---------|----------------|
| `src/pipeline/` | Pipeline orchestration | base, agentic, rag, registry |
| `src/experiment/` | Experiment runner | core, workflows, suite, health, cli |
| `src/config/prompt_domains/` | Domain templates | 8 domains, 45 templates |
| `src/visualization/` | Chart utilities | constants, data_loader, chart_factories |

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
| **RAG** | 5-stage retrieval-augmented | Verification overhead |
| **Hybrid** | Flash + Pro mixed | Cost-quality tradeoff |

### Available Workflows (v3.0)

| Workflow | Type | API Calls | Description |
|----------|------|-----------|-------------|
| `verbosity` | Experiment | Yes | Compare concise vs chain-of-thought |
| `context` | Experiment | Yes | Short vs long context impact |
| `react` | Experiment | Yes | ReAct agent with think-act loops |
| `multiturn` | Experiment | Yes | Multi-turn conversation (3, 5 turns) |
| `self_correcting` | Experiment | Yes | Generate-validate-correct cycles |
| `document` | Experiment | Yes | Document analysis pipelines |
| `rag` | Experiment | Yes | Retrieval-augmented generation |
| `token_profile` | Analysis | No | Token distribution analysis |
| `cost_quality` | Analysis | No | Pareto frontier cost-quality analysis |

### RAG Pipeline Variants (New in v3.0)

| Variant | Retrieval K | Verification | Model Strategy | Cost |
|---------|-------------|--------------|----------------|------|
| `rag_basic` | 5 | No | Flash/Flash | Lowest |
| `rag_verified` | 10 | Yes | Flash/Flash | Medium |
| `rag_hybrid` | 10 | Yes | Flash/Pro | Higher |

### Experimental Design

**Full Suite v3.0**: 1,545 runs across all workflows with streaming, parallel execution, and quality evaluation

---

## 4. Results

### Key Metrics

| Metric | Value |
|--------|-------|
| Pipeline Runs | **1,545** |
| Stage Executions | **3,599** |
| Total Cost | **$16.72** |

### Cost by Model

| Model | Runs | Total Cost | Avg Cost/Run |
|-------|------|------------|--------------|
| Flash | 809 | $4.20 | $0.0052 |
| Pro | 736 | $12.52 | $0.0170 |

**Cost Ratio**: Pro costs **3.3x** more than Flash

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

| Model | Avg Quality |
|-------|-------------|
| Flash | 82.86 |
| Pro | 84.45 |

**Quality Difference**: Pro scores **+1.59** points higher than Flash

### Verified Experiment Results (Ground Truth)

| Difficulty | Flash Accuracy | Pro Accuracy | Pro Advantage |
|------------|---------------|--------------|---------------|
| All | 95% | 100% | +5.3% |
| **Hard** | 60% | 80% | **+33.3%** |

> **Key Finding**: Pro's advantage increases dramatically on hard problems, justifying its 3.3x cost premium for complex reasoning tasks.

---

## 5. Platform Evolution

### Version History

| Version | Phase | Key Features |
|---------|-------|--------------|
| MVP | Initial | Basic cost tracking, vertexai SDK |
| v1.0 | Phase 1-2 | Streaming metrics, parallel execution, quality evaluation |
| v2.0 | Phase 3-4 | google-genai SDK, tiered pricing, session management |
| **v3.0** | Phase 5-6 | RAG pipelines, analysis workflows, modular architecture |

### v3.0 Enhancements

| Enhancement | Description |
|-------------|-------------|
| **SDK Migration** | `vertexai` → `google-genai` with ADC authentication |
| **Tiered Pricing** | Long-context rates (>200K tokens = 2x) |
| **Domain Prompts** | 8 domains: coding, biology, legal, medical, finance, creative, general, complex_reasoning |
| **Ground Truth** | 30 verifiable problems for objective accuracy |
| **RAG Pipelines** | 3 variants for retrieval-augmented generation |
| **Analysis Workflows** | Token profiler, cost-quality Pareto analysis |
| **Modular Architecture** | Large files refactored into packages |

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
6. **Use analysis workflows** — identify optimization opportunities

### Using Analysis Workflows

```bash
# Token distribution analysis
python3 -m src.experiment --workflow token_profile

# Cost-quality Pareto analysis
python3 -m src.experiment --workflow cost_quality --parallel
```

---

## 7. Future Work

### Research Directions

| Direction | Description | Impact |
|-----------|-------------|--------|
| **Benchmark Integration** | GSM8K, MATH, HumanEval for standardized evaluation | Objective model comparison |
| **Multi-Provider Analysis** | OpenAI GPT-4o, Anthropic Claude cost comparison | Cross-provider insights |
| **Caching Optimization** | Measure and optimize prompt cache hit rates | Potential 50%+ savings |
| **Adaptive Routing** | Route queries to optimal model based on complexity | Automated cost/quality tradeoff |

### Engineering Improvements

| Improvement | Description | Priority |
|-------------|-------------|----------|
| **Live API for Verified** | Replace simulated responses with actual Gemini calls | High |
| **RAG Embedding Costs** | Track embedding API costs, retrieval latency | High |
| **Cost Monitoring Dashboard** | Real-time visualization of ongoing experiments | Medium |
| **Cost Budgets** | Run pipelines with hard cost constraints | Medium |

See [07-future-improvements.md](docs/07-future-improvements.md) for the complete roadmap.

---

## 8. Documentation Index

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and quick start |
| [project-demo/README.md](project-demo/README.md) | Detailed usage guide |
| [01-architecture.md](docs/01-architecture.md) | System design & package structure |
| [02-experiments.md](docs/02-experiments.md) | Experiment results & version history |
| [03-pipelines.md](docs/03-pipelines.md) | All 18 pipeline configurations |
| [04-recommendations.md](docs/04-recommendations.md) | Cost optimization strategies |
| [05-troubleshooting.md](docs/05-troubleshooting.md) | Common errors and solutions |
| [06-new-workflows.md](docs/06-new-workflows.md) | RAG, Token Profiler, Cost-Quality |
| [07-future-improvements.md](docs/07-future-improvements.md) | Planned enhancements |
| [00-project-mvp.md](docs/00-project-mvp.md) | Historical MVP reference (archived) |

---

## Appendix: CLI Reference

### Session Management
```bash
python3 -m src.session new "experiment_name"   # Create isolated session
python3 -m src.session list                     # List all sessions
python3 -m src.session current                  # Show current session
```

### Experiments
```bash
# Full suite (recommended)
python3 -m src.experiment --full-experiment

# Specific workflow
python3 -m src.experiment --workflow react --model flash --iterations 20

# RAG experiment
python3 -m src.experiment --workflow rag --model flash --iterations 10

# Analysis workflows (no API calls)
python3 -m src.experiment --workflow token_profile
python3 -m src.experiment --workflow cost_quality --parallel

# Domain experiments
python3 -m src.experiments.domain_experiment --domain complex_reasoning --compare-models

# Verified experiments (ground truth)
python3 -m src.experiments.verified_experiment --compare-models -n 20 -d hard

# Utilities
python3 -m src.experiment --health-check
python3 -m src.experiment --list-pipelines
python3 -m src.experiment --estimate-cost
```

### Report Generation
```bash
python3 notebooks/generate_report.py           # Generate all figures + summary
```

---

**Platform v3.0** | December 2025 | [Detailed Docs](docs/) | [Demo README](project-demo/README.md)

