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
cd llm-cost-mvp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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
│   ├── config/                   # Configuration module
│   │   ├── models.py            # Model IDs, pricing, GCP config
│   │   ├── prompts.py           # Prompt templates with A/B variants
│   │   ├── test_data.py         # Queries, contexts
│   │   └── documents.py         # Document loader for test files
│   ├── clients/                  # API clients
│   │   └── vertex.py            # Vertex AI + streaming support
│   ├── pipelines/                # Pipeline orchestration
│   │   ├── base.py              # Base classes and types
│   │   └── __init__.py          # Re-exports from legacy
│   ├── evaluation/               # Quality assessment
│   │   └── automated.py         # Automated + LLM evaluation
│   ├── db/                       # Database operations
│   │   ├── connection.py        # Thread-safe connections (WAL)
│   │   ├── schema.py            # Table definitions
│   │   ├── write.py             # Insert operations
│   │   └── query.py             # Read + A/B test analysis
│   ├── experiments/              # Experiment runners
│   │   └── ab_testing.py        # A/B test framework
│   ├── utils/                    # Utilities
│   │   └── cost.py              # Cost calculations
│   ├── pipeline.py              # Legacy pipeline definitions
│   ├── experiment.py            # Legacy CLI runner
│   └── config.py                # Legacy config (backwards compat)
├── test_documents/               # Real test files for analysis
│   ├── code/                    # Python source files
│   ├── configs/                 # YAML, JSON, Terraform, Docker
│   ├── docs/                    # HTML, Markdown documents  
│   └── reports/                 # PDF security reports
├── notebooks/
│   └── analysis.ipynb           # Analysis notebook
└── data/
    └── experiments.db           # SQLite database
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
| **Prompt Variants** | Which prompt style gives best cost-quality ratio? |

---

## A/B Testing for Prompt Engineering

The platform includes a comprehensive A/B testing framework for comparing prompt variants.

### Prompt Templates with Variants

Each prompt template supports multiple variants:

```python
from src.config import get_prompt

# Get a prompt template
generation = get_prompt("generation")

# Available variants
print(generation.list_variants())
# ['control', 'concise', 'detailed', 'structured', 'cot', 'persona']

# Render with specific variant
prompt = generation.render(variant="detailed", query="What is machine learning?")
```

### Pre-defined A/B Tests

```bash
# List available tests
python3 -c "from src.experiments import list_ab_tests; print(list_ab_tests())"
# ['generation_style', 'critique_depth', 'extraction_format', 'validation_strictness']
```

### Running A/B Tests

```python
from src.experiments import run_ab_test_by_name, run_custom_ab_test

# Run a pre-defined test
results = run_ab_test_by_name(
    "generation_style",
    model="flash",
    iterations_per_variant=20,
    parallel=True,
)

# Run a custom test
results = run_custom_ab_test(
    prompt_name="critique",
    variants=["control", "detailed", "socratic"],
    model="flash",
    iterations=15,
)
```

### Analyzing Results

```python
from src.experiments import print_ab_test_analysis
from src.db import get_ab_test_summary, get_ab_test_quality

# Print analysis
print_ab_test_analysis("generation_style")

# Get DataFrames for custom analysis
summary = get_ab_test_summary("generation_style")
quality = get_ab_test_quality("generation_style")
```

### Prompt Variant Types

| Variant | Description |
|---------|-------------|
| `control` | Baseline prompt |
| `concise` | Shorter, more direct |
| `detailed` | Comprehensive instructions |
| `structured` | Explicit output format |
| `cot` | Chain-of-thought style |
| `persona` | With role/persona |
| `few_shot` | With examples |

---

## Test Documents

The platform includes realistic test documents in various formats for security analysis experiments:

### Document Catalog

| ID | Type | File | Description |
|----|------|------|-------------|
| `python_auth` | Python | `code/user_auth.py` | Auth module with SQL injection, plaintext passwords |
| `python_api` | Python | `code/api_server.py` | Flask API with command injection, XSS, file upload |
| `k8s_deployment` | YAML | `configs/kubernetes-deployment.yaml` | K8s config with privileged containers, exposed secrets |
| `terraform_aws` | Terraform | `configs/aws-infrastructure.tf` | AWS IaC with public S3, open security groups |
| `docker_compose` | YAML | `configs/docker-compose.yaml` | Docker config with socket mounts, root containers |
| `dockerfile` | Dockerfile | `configs/Dockerfile` | Build file with hardcoded secrets, no multi-stage |
| `json_config` | JSON | `configs/app-config.json` | App config with API keys, passwords, debug flags |
| `html_login` | HTML | `docs/login-page.html` | Login page with XSS, localStorage credentials |
| `md_architecture` | Markdown | `docs/architecture-spec.md` | Architecture doc with exposed credentials |
| `pdf_audit` | PDF | `reports/security-audit-q4-2024.pdf` | Security audit with credentials in findings |
| `pdf_incident` | PDF | `reports/incident-report-2024-0042.pdf` | Incident report with breach details |

### Loading Documents

```python
from src.config import load_catalog_document, list_catalog, load_all_test_documents

# List available documents
for doc in list_catalog():
    print(f"{doc['id']}: {doc['name']} ({doc['type']})")

# Load a specific document
doc = load_catalog_document("python_auth")
print(doc.content)

# Load all documents
all_docs = load_all_test_documents()
```

### Running Document Analysis

```bash
# Analyze with real test documents
python3 -m src.experiment --workflow document --model flash --iterations 10

# With parallel execution
python3 -m src.experiment --workflow document --model pro --iterations 20 --parallel
```

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
--full-suite          # Run all workflows with specified settings
--full-experiment     # Complete package: 20 iters, 16 workers, streaming, LLM eval, A/B tests
--list-pipelines      # Show all available pipelines
--summary             # Show existing results
--reset               # Clear database before running
--test-connection     # Verify Vertex AI access
--test-streaming      # Verify streaming works
```

### Quick Start: Full Experiment

Run the complete experiment suite with one command:

```bash
# This runs:
# - All 6 workflows (verbosity, context, react, multiturn, self_correcting, document)
# - Both models (Flash + Pro)
# - 20 iterations per variant
# - 16 parallel workers
# - Streaming enabled (TTFT metrics)
# - LLM quality evaluation
# - All A/B tests (generation_style, critique_depth, extraction_format, validation_strictness)

python3 -m src.experiment --full-experiment
```

Estimated runtime: ~30-60 minutes depending on API rate limits.

---

## Models

| Model | ID | Input Price | Output Price |
|-------|-----|-------------|--------------|
| Flash | gemini-2.5-flash | $0.15/1M tokens | $0.60/1M tokens |
| Pro | gemini-2.5-pro | $1.25/1M tokens | $5.00/1M tokens |

---

## Author

Anh Dao — Aalto University
