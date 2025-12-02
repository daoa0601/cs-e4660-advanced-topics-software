# LLM Cost Decomposition Platform (MVP)

**Course Project** — Aalto University, Advanced Topics in Software  
**Focus**: Empirical LLM cost measurement with agentic workflows  
**Date**: January 2025

---

## Overview

A platform demonstrating **granular cost tracking** for complex LLM workflows including:

- **Multi-stage pipelines** with per-stage cost attribution
- **Multi-model hybrid** pipelines (e.g., Flash for drafts, Pro for critique)
- **Agentic patterns** (ReAct loops, multi-turn conversations, self-correcting)
- **Document analysis** workflows (security review, vulnerability detection)
- **Streaming metrics** (Time-to-First-Token, throughput)
- **Parallel execution** for faster experimentation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Experiment Runner                          │
│              (Sequential or Parallel Execution)                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Linear:     [Stage1] ──▶ [Stage2] ──▶ [Stage3]          │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ReAct:      [Think] ──▶ [Act] ──▶ [Think] ──▶ ... loop  │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Multi-Turn: [Turn1] ──▶ [Turn2] ──▶ [Turn3] (growing)   │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Self-Correct: [Gen] ──▶ [Validate] ──▶ [Fix] ──▶ loop   │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Document:   [Extract] ──▶ [Analyze] ──▶ [Recommend]     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌──────────────┐        ┌──────────────┐          ┌──────────────┐
│   Vertex AI  │        │   Quality    │          │   Streaming  │
│    Client    │        │  Evaluator   │          │   Metrics    │
│  (streaming) │        │              │          │  (TTFT, TPS) │
└──────┬───────┘        └──────┬───────┘          └──────┬───────┘
       │                       │                         │
       └───────────────────────┼─────────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   SQLite Database   │
                    │   (WAL mode for     │
                    │   concurrent access)│
                    │  ┌───────────────┐  │
                    │  │ runs          │  │  ← iterations, turns, termination
                    │  │ stages        │  │  ← TTFT, tokens/sec, iteration#
                    │  │ quality_scores│  │
                    │  └───────────────┘  │
                    └─────────────────────┘
```

---

## Pipeline Types

### 1. Linear Pipelines (Standard)

| Pipeline | Stages | Description |
|----------|--------|-------------|
| `verbosity_concise` | 1 | Direct generation |
| `verbosity_cot` | 3 | Draft → Critique → Refine |
| `context_short` | 2 | Extract → Summarize |
| `context_long` | 3 | Extract → Summarize → Evaluate |

### 2. Multi-Model Hybrid

| Pipeline | Stages | Models |
|----------|--------|--------|
| `hybrid_cot` | 3 | Flash (draft) → **Pro** (critique) → Flash (refine) |

**Cost Optimization**: Use expensive models only where they add value.

### 3. Agentic Patterns

| Pipeline | Pattern | Description |
|----------|---------|-------------|
| `react_research` | ReAct Loop | Think → Act → Observe (max 5 iterations) |
| `react_hybrid` | ReAct Hybrid | **Pro** (think) → Flash (act) |
| `multiturn_3` | Conversation | 3-turn with context accumulation |
| `multiturn_5` | Conversation | 5-turn with context growth tracking |
| `self_correcting` | Validate Loop | Generate → Validate → Fix (max 3 retries) |
| `self_correcting_hybrid` | Validate Hybrid | Flash (generate) → **Pro** (validate) |

### 4. Document Analysis

| Pipeline | Stages | Strategy |
|----------|--------|----------|
| `doc_analysis_simple` | 2 | Extract → Analyze |
| `doc_analysis_thorough` | 4 | Extract → Analyze → Classify → Recommend |
| `doc_analysis_iterative` | 3 | Analyze → Self-Review → Refine |
| `doc_analysis_hybrid` | 3 | Flash (extract) → **Pro** (analyze) → Flash (remediate) |

**Use Case**: Security vulnerability detection in code, configs, and architecture docs.

---

## Features

### Per-Stage Cost Attribution

Track where money goes within each pipeline:
```
Pipeline: verbosity_cot
  Stage 1 (draft):    $0.000234  ← generation
  Stage 2 (critique): $0.000456  ← critique (most expensive!)
  Stage 3 (refine):   $0.000321  ← refinement
  Total:              $0.001011
```

### Streaming Metrics

Capture user-perceived latency:
```
Time to First Token (TTFT): 145ms  ← User sees response start
Total Latency:              892ms  ← Full response complete
Throughput:                 67.3 tokens/sec
```

### Agentic Loop Tracking

Understand iteration costs:
```
ReAct Pipeline:
  Iterations: 3 (terminated: confidence_reached)
  Total cost: $0.002341
  Cost per iteration: $0.000780
```

### Context Growth Analysis

Multi-turn cost escalation:
```
Turn 1: 500 input tokens  → $0.0001
Turn 2: 1,200 input tokens → $0.0003  (context growing!)
Turn 3: 2,100 input tokens → $0.0005
Turn 4: 3,200 input tokens → $0.0008
Turn 5: 4,500 input tokens → $0.0012
```

### Parallel Execution

Run experiments faster with concurrent API calls:
```bash
# Sequential (default): ~20 min for 100 iterations
python3 -m src.experiment --workflow verbosity --model flash --iterations 100

# Parallel: ~5 min for 100 iterations (4 workers)
python3 -m src.experiment --workflow verbosity --model flash --iterations 100 --parallel

# Parallel with 8 workers: ~3 min
python3 -m src.experiment --full-suite --iterations 20 --parallel --workers 8
```

---

## Quick Start

### 1. Setup

```bash
git clone <repository-url>
cd project-demo
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env.example .env  # Add your GCP_PROJECT_ID
```

### 2. Test Connection

```bash
python3 -m src.experiment --test-connection
python3 -m src.experiment --test-streaming
```

### 3. List Pipelines

```bash
python3 -m src.experiment --list-pipelines
```

### 4. Run Experiments

```bash
# Single workflow
python3 -m src.experiment --workflow verbosity --model flash --iterations 10

# With streaming metrics
python3 -m src.experiment --workflow react --model flash --iterations 5 --streaming

# Agentic workflows
python3 -m src.experiment --workflow multiturn --model flash --iterations 10
python3 -m src.experiment --workflow self_correcting --model flash --iterations 10

# Document analysis
python3 -m src.experiment --workflow document --model flash --iterations 10

# Full suite (all workflows, both models)
python3 -m src.experiment --full-suite --iterations 10 --streaming

# Full suite with parallel execution (much faster!)
python3 -m src.experiment --full-suite --iterations 20 --parallel --workers 8

# Reset database before running
python3 -m src.experiment --reset
```

### 5. Analyze Results

```bash
jupyter notebook notebooks/analysis.ipynb
```

---

## Project Structure

```
llm-cost-mvp/
├── src/
│   ├── config.py             # Pricing, prompts, test documents
│   ├── vertex_client.py      # Vertex AI + streaming support
│   ├── cost_calculator.py    # Cost computation
│   ├── pipeline.py           # All pipeline types (15 pipelines)
│   ├── evaluator.py          # Quality evaluation
│   ├── db.py                 # Thread-safe DB with WAL mode
│   └── experiment.py         # CLI with parallel execution
├── notebooks/
│   └── analysis.ipynb        # Comprehensive analysis
└── data/
    └── experiments.db
```

---

## Database Schema

### `runs` — Pipeline executions
```sql
-- Standard fields
id, timestamp, workflow, pipeline, model, total_cost, ...

-- Agentic metadata
pipeline_type TEXT,        -- 'linear', 'react', 'multiturn', 'self_correcting'
iterations INTEGER,        -- Number of loop iterations
turns INTEGER,             -- Number of conversation turns
termination_reason TEXT,   -- 'max_iterations', 'confidence_reached', 'validation_passed'
avg_ttft_ms FLOAT,         -- Average time to first token
context_tokens_by_turn TEXT -- JSON array of context sizes
```

### `stages` — Per-stage with streaming
```sql
-- Standard fields
run_id, stage_order, stage_name, stage_type, model, cost, ...

-- Loop/turn tracking
iteration INTEGER,         -- Which iteration (for ReAct/self-correcting)
turn INTEGER,              -- Which turn (for multi-turn)

-- Streaming metrics
time_to_first_token_ms INTEGER,
tokens_per_second FLOAT
```

---

## Key Analyses

| Analysis | Question |
|----------|----------|
| **Cost Attribution** | Which stage types consume the most budget? |
| **Hybrid Efficiency** | Does mixing models reduce cost without hurting quality? |
| **Iteration Cost** | How much does each ReAct iteration cost? |
| **Context Growth** | How fast do multi-turn costs escalate? |
| **TTFT vs Latency** | Is user-perceived speed different from total time? |
| **Cost-Quality** | Which pipelines offer best quality per dollar? |
| **Document Strategy** | Is thorough analysis worth 2x the cost of simple? |

---

## CLI Reference

```bash
# Workflows
--workflow verbosity|context|react|multiturn|self_correcting|document

# Models
--model flash|pro

# Options
--iterations N        # Runs per variant (default: 20)
--delay N             # Seconds between API calls (default: 0.5)
--streaming           # Enable TTFT metrics
--llm-eval            # Use LLM for quality scoring (costs extra)
--parallel            # Run iterations concurrently
--workers N           # Number of parallel workers (default: 4)

# Commands
--full-suite          # Run everything
--list-pipelines      # Show all available pipelines
--summary             # Show existing results
--reset               # Clear database before running
--test-connection     # Verify Vertex AI access
--test-streaming      # Verify streaming works
```

---

## Models

| Model | ID | Input Price | Output Price |
|-------|-----|-------------|--------------|
| Flash | gemini-2.5-flash | $0.15/1M tokens | $0.60/1M tokens |
| Pro | gemini-2.5-pro | $1.25/1M tokens | $5.00/1M tokens |

---

## Author

Anh Dao — Aalto University
