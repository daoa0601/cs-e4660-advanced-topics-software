# System Architecture

**Version:** 3.0  
**Last Updated:** December 2025

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Provider | Google Vertex AI | Gemini 2.5 Flash & Pro |
| SDK | google-genai (v0.3+) | Unified API with ADC |
| Embeddings | text-embedding-004 | RAG semantic search |
| Vector Store | FAISS | Local similarity search |
| Database | SQLite (WAL mode) | Thread-safe storage |
| Analysis | Pandas, Plotly | Data visualization |
| Logging | Python logging | Structured, configurable logging |

---

## Architecture Diagram

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
│    Linear | ReAct | Multi-Turn | Self-Correct | RAG | A/B       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
      ┌──────────┐       ┌──────────┐       ┌──────────┐
      │ GenAI    │       │ Quality  │       │ Streaming│
      │ Client   │       │ Evaluator│       │ Metrics  │
      │          │       │          │       │          │
      │  Flash/  │       │ LLM-based│       │  TTFT    │
      │   Pro    │       │ + Ground │       │ tracking │
      └────┬─────┘       │ Truth    │       └────┬─────┘
           │             └────┬─────┘            │
           └──────────────────┼──────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
   ┌────────────────────┐         ┌────────────────────┐
   │  SQLite Database   │         │   Visualization    │
   │    src/db/         │         │ src/visualization/ │
   └────────────────────┘         └────────────────────┘
```

---

## Project Structure (v3.0)

The codebase follows a modular package architecture:

```
project-demo/
├── src/
│   ├── pipeline/                    # Pipeline orchestration (refactored)
│   │   ├── __init__.py              # Re-exports for backward compatibility
│   │   ├── base.py                  # StageType, PipelineStage, Pipeline
│   │   ├── agentic.py               # ReActPipeline, MultiTurnPipeline, SelfCorrectingPipeline
│   │   ├── rag.py                   # RAGPipeline class (real FAISS retrieval)
│   │   └── registry.py              # 18 pipeline instances + get_pipeline()
│   │
│   ├── rag/                         # RAG components (NEW)
│   │   ├── embedding_client.py      # Google GenAI text-embedding-004
│   │   ├── vector_store.py          # FAISS with disk persistence
│   │   ├── chunker.py               # Document chunking utilities
│   │   └── cost_tracker.py          # Embedding cost tracking
│   │
│   ├── experiment/                  # Experiment runner (refactored)
│   │   ├── __init__.py              # Re-exports
│   │   ├── __main__.py              # Entry point
│   │   ├── core.py                  # run_workflow_experiment(), _run_single_iteration()
│   │   ├── workflows.py             # All 7 workflow functions
│   │   ├── suite.py                 # run_full_suite(), run_full_experiment()
│   │   ├── health.py                # run_health_check(), estimate_experiment_cost()
│   │   ├── logging.py               # log_pipeline_result()
│   │   ├── summary.py               # _print_full_summary()
│   │   └── cli.py                   # main(), argument parsing
│   │
│   ├── experiments/                 # Specialized experiments
│   │   ├── verified_experiment.py   # Ground truth (real API calls)
│   │   ├── domain_experiment.py     # Domain-specific (real API calls)
│   │   └── ab_testing.py            # A/B testing
│   │
│   ├── config/
│   │   ├── prompt_domains/          # Domain templates (refactored)
│   │   │   ├── models.py            # PromptTemplate, DomainConfig
│   │   │   ├── data.py              # 8 domain configurations
│   │   │   └── registry.py          # get_domain(), list_domains()
│   │   └── verifiable_problems.py   # Ground truth problems
│   │
│   ├── evaluation/
│   │   ├── vulnerabilities/         # Vulnerability data (refactored)
│   │   │   ├── models.py            # Severity, Vulnerability, DocumentVulnerabilities
│   │   │   ├── data.py              # 9 document vulnerability definitions
│   │   │   └── queries.py           # get_vulnerabilities(), calculate_detection_score()
│   │   └── verified_experiment.py   # Ground truth experiments
│   │
│   ├── visualization/               # Chart utilities (NEW in v3.0)
│   │   ├── constants.py             # Color palettes, style constants
│   │   ├── data_loader.py           # Cached data loading
│   │   └── chart_factories.py       # Chart generation functions
│   │
│   ├── clients/                     # LLM clients
│   │   └── genai_client.py          # google-genai SDK wrapper
│   │
│   ├── db/                          # Database operations
│   │   ├── connection.py            # SQLite connection management
│   │   └── queries.py               # CRUD operations
│   │
│   ├── pricing/                     # Cost calculation
│   │   └── tiered_pricing.py        # Context-aware pricing (200K threshold)
│   │
│   ├── cost_calculator.py           # Cost calculation orchestration
│   ├── evaluator.py                 # Quality evaluation
│   ├── session.py                   # Session management
│   └── logging_config.py            # Structured logging
│
├── scripts/                         # Utility scripts
│   ├── generate_academic_corpus.py  # Generate RAG knowledge base
│   └── build_rag_index.py           # Build FAISS index
│
├── notebooks/                       # Analysis notebooks
│   ├── analysis.ipynb               # Interactive analysis
│   ├── generate_report.py           # Automated figure generation
│   └── flash_vs_pro_analysis.py     # Model comparison
│
├── sessions/                        # Isolated experiment runs
├── figures/                         # Generated visualizations
├── data/                            # Default database + FAISS index
└── test-docs/                       # RAG corpus files
```

---

## Modular Design Principles

The v3.0 refactoring followed these principles:

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | Each module has one clear purpose |
| **Backward Compatibility** | `__init__.py` re-exports maintain old imports |
| **Registry Pattern** | Pipelines and domains use centralized registries |
| **Separation of Concerns** | Data, business logic, and presentation separated |

---

## Pricing (December 2025)

| Model | Tier | Input (/1M) | Output (/1M) |
|-------|------|-------------|--------------|
| Flash | Standard (≤200K) | $0.15 | $0.60 |
| | Long Context (>200K) | $0.30 | $1.20 |
| Pro | Standard (≤200K) | $1.25 | $10.00 |
| | Long Context (>200K) | $2.50 | $15.00 |

**Formula**: `cost = (input_tokens × input_rate) + (output_tokens × output_rate)`

---

## Database Schema

```sql
-- runs: Pipeline-level metrics
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    workflow TEXT, pipeline TEXT, model TEXT,
    total_cost REAL, total_latency_ms INTEGER,
    iterations INTEGER, turns INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- stages: Stage-level cost attribution
CREATE TABLE stages (
    run_id INTEGER, stage_name TEXT, model TEXT,
    cost REAL, input_tokens INTEGER, output_tokens INTEGER,
    iteration INTEGER, turn INTEGER,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- Indexes for performance (added in Phase 4)
CREATE INDEX idx_runs_workflow_model ON runs(workflow, model);
CREATE INDEX idx_stages_run_turn ON stages(run_id, turn);
CREATE INDEX idx_runs_timestamp ON runs(timestamp);
CREATE INDEX idx_stages_run_iteration ON stages(run_id, iteration);
```

---

## Related Documentation

- [03-pipelines.md](03-pipelines.md) - Pipeline implementations and variants
- [06-new-workflows.md](06-new-workflows.md) - RAG, Token Profiler, Cost-Quality workflows
- [05-troubleshooting.md](05-troubleshooting.md) - Common issues and solutions

