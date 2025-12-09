# Project MVP Phase

> [!NOTE]
> **ARCHIVED** — This document describes the historical MVP phase. For current development, see [project-demo/](../project-demo/) (v3.0).

This document describes the MVP (Minimum Viable Product) phase of the LLM Cost Decomposition Platform, which established the foundational architecture before the enhanced demo phase.

---

## Overview

The MVP phase (`project-mvp/`) implemented the core cost tracking infrastructure with basic pipeline support and initial experiments.

**Status:** Archived (historical reference)  
**Phase Duration:** Initial development  
**Runs Completed:** 591  
**Total Cost:** $6.40  

---

## MVP Features

| Feature | Description |
|---------|-------------|
| **Cost Calculation** | Per-token cost tracking with Vertex AI pricing |
| **Pipeline Types** | Linear, ReAct, Multi-Turn, Self-Correcting |
| **Database** | SQLite storage for runs and stages |
| **Basic Experiments** | Verbosity, context growth, agent patterns |

---

## Key Learnings

These findings from the MVP phase informed the design of the current platform:

1. **Flash vs Pro Cost Ratio**: Consistent 7.5x cost difference across pipeline types
2. **Stage Cost Distribution**: Generation (45%), Conversation (25%), Thinking (15%), Critique (10%), Refinement (5%)
3. **Context Growth**: Turn 5 costs ~8x Turn 1 due to context accumulation
4. **Agent Variability**: ReAct shows 5x cost variance based on query complexity

---

## MVP Structure

```
project-mvp/          # ARCHIVED
├── src/
│   ├── cost_calculator.py    # Basic cost calculation
│   ├── pipeline.py           # Core pipeline types
│   └── experiment.py         # Basic experiment runner
├── data/                     # SQLite database
└── notebooks/               # Analysis notebooks
```

---

## Evolution to Current Platform (v3.0)

The current platform (`project-demo/` v3.0) evolved from MVP through 6 phases of improvements:

| Phase | Focus | Key Additions |
|-------|-------|---------------|
| 1 | Critical Fixes | Retry logic, unit tests |
| 2 | Code Quality | Consolidated runners, structured logging |
| 3 | UX Improvements | CLI validation, cost estimation, health checks |
| 4 | Performance | Database indexes, environment configuration |
| 5 | New Features | RAG pipeline, Token Profiler, Cost-Quality analysis |
| 6 | Refactoring | Modular package architecture |

### Key Enhancements Over MVP

- **SDK Migration**: `vertexai` → `google-genai` with ADC
- **Tiered Pricing**: Context-aware pricing (>200K = 2x rate)
- **Streaming Metrics**: TTFT (Time to First Token) tracking
- **Quality Evaluation**: LLM-based scoring and ground truth verification
- **Session Management**: Isolated experiment runs
- **Parallelization**: Multi-worker experiment execution
- **New Workflows**: RAG, Token Profiler, Cost-Quality Analysis
- **Modular Architecture**: Large files refactored into packages

See [02-experiments.md](02-experiments.md) for detailed comparison of MVP vs current results.

---

## Current Development

For active development, refer to:
- [project-demo/README.md](../project-demo/README.md) - Usage guide
- [01-architecture.md](01-architecture.md) - Current architecture
- [02-experiments.md](02-experiments.md) - Development history (Phases 1-6)

