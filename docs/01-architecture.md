# System Architecture

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Provider | Google Vertex AI | Gemini 2.5 Flash & Pro |
| SDK | google-genai (v0.3+) | Unified API with ADC |
| Database | SQLite (WAL mode) | Thread-safe storage |
| Analysis | Pandas, Plotly | Data visualization |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                 Experiment Runner                    │
│     --workflow, --model, --iterations, --parallel   │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               Pipeline Orchestrator                  │
│  Linear | ReAct | Multi-Turn | Self-Correct | A/B   │
└────────────────────────┬────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │ Vertex  │    │ Quality  │    │ Streaming│
    │ Client  │    │ Evaluator│    │ Metrics  │
    └────┬────┘    └─────┬────┘    └────┬─────┘
         └───────────────┴───────────────┘
                         │
                         ▼
              ┌────────────────────┐
              │  SQLite Database   │
              └────────────────────┘
```

## Pricing (December 2025)

| Model | Tier | Input (/1M) | Output (/1M) |
|-------|------|-------------|--------------|
| Flash | Standard (≤200K) | $0.15 | $0.60 |
| | Long Context (>200K) | $0.30 | $1.20 |
| Pro | Standard (≤200K) | $1.25 | $10.00 |
| | Long Context (>200K) | $2.50 | $15.00 |

**Formula**: `cost = (input_tokens × input_rate) + (output_tokens × output_rate)`

## Database Schema

```sql
-- runs: Pipeline-level metrics
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    workflow TEXT, pipeline TEXT, model TEXT,
    total_cost REAL, total_latency_ms INTEGER,
    iterations INTEGER, turns INTEGER
);

-- stages: Stage-level cost attribution
CREATE TABLE stages (
    run_id INTEGER, stage_name TEXT, model TEXT,
    cost REAL, input_tokens INTEGER, output_tokens INTEGER
);
```
