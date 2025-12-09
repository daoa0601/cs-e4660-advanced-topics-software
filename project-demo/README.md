# LLM Cost Decomposition Platform

Granular cost analysis for multi-stage LLM pipelines using Gemini 2.5 Flash & Pro.

## Quick Start

```bash
# 1. Setup
pip install -r requirements.txt
cp .env.example .env  # Add your GCP_PROJECT_ID

# 2. Run experiments
python3 -m src.experiment --full-experiment

# 3. Generate report
python3 notebooks/generate_report.py
```

---

## Running Experiments

### Full Suite (Recommended)

```bash
python3 -m src.experiment --full-experiment
```

This runs:
- All workflows (verbosity, context, react, multiturn, self_correcting, document, rag)
- Both models (Flash & Pro)
- 20 iterations each
- 16 parallel workers
- Streaming metrics (TTFT)
- LLM quality evaluation
- A/B testing

### Available Workflows

| Workflow | Type | Description |
|----------|------|-------------|
| `verbosity` | Experiment | Compare concise vs chain-of-thought prompts |
| `context` | Experiment | Short vs long context length impact |
| `react` | Experiment | ReAct agent with think-act loops |
| `multiturn` | Experiment | Multi-turn conversation (3 and 5 turns) |
| `self_correcting` | Experiment | Generate-validate-correct cycles |
| `document` | Experiment | Document analysis pipelines |
| `rag` | Experiment | RAG with real FAISS embeddings (requires index) |
| `token_profile` | Analysis | Analyze token distribution patterns (no API calls) |
| `cost_quality` | Analysis | Pareto frontier cost-quality analysis (no API calls) |

### Individual Workflows

```bash
# Run specific workflow
python3 -m src.experiment --workflow react --model flash --iterations 10

# With streaming metrics
python3 -m src.experiment --workflow verbosity --model pro --streaming

# RAG experiment (retrieval-augmented generation)
python3 -m src.experiment --workflow rag --model flash --iterations 5

# Analysis workflows (no API calls required)
python3 -m src.experiment --workflow token_profile
python3 -m src.experiment --workflow cost_quality --parallel

# See all options
python3 -m src.experiment --help

# List available pipelines
python3 -m src.experiment --list-pipelines
```

---

## Session Management (Isolate Experiment Runs)

Keep each experiment run in a separate folder:

```bash
# Create new session
python3 -m src.session new "experiment_name"

# Run experiments (uses session's database)
python3 -m src.experiment --full-experiment

# Generate report (saves to session's figures folder)
python3 notebooks/generate_report.py

# List all sessions
python3 -m src.session list

# Switch to existing session
python3 -m src.session use "session_name"

# Show current session
python3 -m src.session current

# Archive current and start fresh
python3 -m src.session archive
```

Session structure:
```
sessions/
├── experiment_name_20251206_1500/
│   ├── data/experiments.db
│   ├── figures/*.png
│   └── session_info.json
```

---

## Generating Reports

After experiments complete:

```bash
python3 notebooks/generate_report.py
```

Generates:
- `figures/01_cost_by_model.png` - Cost comparison
- `figures/02_cost_by_pipeline.png` - Per-pipeline costs
- `figures/03_quality_by_model.png` - Quality scores
- `figures/04_cost_quality_scatter.png` - Cost vs quality
- `figures/05_stage_cost_distribution.png` - Stage breakdown
- `figures/06_pro_vs_flash_advantage.png` - Pro advantages
- `figures/07_verified_accuracy.png` - Ground truth accuracy
- `figures/summary.md` - Key metrics summary

---

## Verified Experiments (Ground Truth)

Run problems with known correct answers:

```bash
# Compare Flash vs Pro accuracy
python3 -m src.experiments.verified_experiment --compare-models -n 20

# Hard problems only (where Pro shines)
python3 -m src.experiments.verified_experiment --compare-models -d hard -n 10
```

> **Note**: All experiments now use real Gemini API calls (no simulation).

---

## RAG Setup (FAISS Vector Store)

The RAG pipeline uses real semantic embeddings. Before running RAG experiments:

```bash
# 1. Generate academic corpus (~200 research chunks)
python3 scripts/generate_academic_corpus.py --chunks 200

# 2. Build FAISS index
python3 scripts/build_rag_index.py

# 3. Run RAG experiments
python3 -m src.experiment --workflow rag --iterations 5
```

Index is persisted to `data/faiss/` for reuse.

---

## Tiered Pricing

Cost calculations use context-aware tiered pricing:

| Tier | Context Size | Flash Input/Output | Pro Input/Output |
|------|--------------|-------------------|------------------|
| Standard | ≤200K tokens | $0.15 / $0.60 | $1.25 / $10.00 |
| Long-Context | >200K tokens | $0.30 / $1.20 | $2.50 / $15.00 |

Multi-turn conversations automatically detect when context exceeds 200K tokens and apply long-context rates.

---

## Additional Experiment Types

### A/B Testing (Prompt Variants)

Compare different prompt strategies:

```bash
# Run A/B test on prompt variants
python3 -m src.experiments.ab_testing --iterations 10
```

### Domain Experiments

Test performance across specialized domains:

```bash
# Run domain-specific experiments
python3 -m src.experiments.domain_experiment --domain coding -n 10

# Available domains: coding, biology, legal, creative, finance, medical
python3 -m src.experiments.domain_experiment --compare-domains
```

---

## Project Structure

```
project-demo/
├── src/
│   ├── experiment.py          # Main CLI entry point
│   ├── session.py             # Session management
│   ├── cost_calculator.py     # Cost calculation (uses tiered pricing)
│   ├── pipeline.py            # Pipeline orchestration
│   ├── evaluator.py           # Quality evaluation
│   ├── clients/               # LLM client (google-genai SDK with Vertex AI)
│   ├── pricing/               # Tiered pricing engine (200K token threshold)
│   ├── config/                # Model configs, prompts, verifiable problems
│   ├── experiments/           # A/B testing, domain, and verified experiments
│   ├── rag/                   # RAG components (embeddings, FAISS, chunking)
│   └── pipeline/              # Pipeline implementations (linear, agentic, RAG)
├── scripts/
│   ├── generate_academic_corpus.py  # Generate RAG knowledge base
│   └── build_rag_index.py           # Build FAISS index
├── notebooks/
│   ├── analysis.ipynb         # Jupyter analysis
│   ├── generate_report.py     # Auto-generate figures
│   └── flash_vs_pro_analysis.py
├── figures/                   # Generated visualizations
├── sessions/                  # Isolated experiment runs
├── data/                      # Default database + FAISS index
└── test-docs/                 # RAG corpus files
```

---

## Key Commands Reference

| Command | Description |
|---------|-------------|
| `--full-experiment` | Complete suite with all options |
| `--full-suite` | All workflows, both models |
| `--workflow X` | Single workflow |
| `--model flash/pro` | Specific model |
| `--iterations N` | Number of runs |
| `--parallel --workers N` | Parallel execution |
| `--streaming` | Capture TTFT metrics |
| `--llm-eval` | Enable quality scoring |
| `--list-pipelines` | Show available pipelines |
| `--summary` | Show existing run stats |
| `--reset` | Clear database |
| `--health-check` | Verify database, API, config, and pipelines |
| `--estimate-cost` | Preview experiment cost without running |
| `--log-level` | Set logging level (DEBUG, INFO, WARNING, ERROR) |

---

## Verify Setup

Before running experiments, verify your environment:

```bash
python3 -m src.experiment --health-check
```

This checks:
- Database connection and schema
- API connectivity (Vertex AI)
- Configuration files
- Available pipelines

---

## Cost Preview

Estimate costs before running experiments:

```bash
# Estimate cost for a specific workflow
python3 -m src.experiment --workflow react --model flash --iterations 10 --estimate-cost

# Estimate full experiment cost
python3 -m src.experiment --full-experiment --estimate-cost
```

---

## Debugging

Control logging verbosity:

```bash
# Verbose output for debugging
python3 -m src.experiment --workflow verbosity --model flash --log-level DEBUG

# Quiet mode (warnings and errors only)
python3 -m src.experiment --full-experiment --log-level WARNING
```

Available log levels: `DEBUG`, `INFO` (default), `WARNING`, `ERROR`

---

## Documentation

See [LLM_Cost_Decomposition_Platform_Report.md](../LLM_Cost_Decomposition_Platform_Report.md) for detailed findings.

### Reference Documentation

| Document | Description |
|----------|-------------|
| [Architecture](../docs/01-architecture.md) | System design & package structure |
| [Experiments](../docs/02-experiments.md) | Experiment results & version history |
| [Pipelines](../docs/03-pipelines.md) | All 18 pipeline configurations |
| [Recommendations](../docs/04-recommendations.md) | Cost optimization strategies |
| [Troubleshooting](../docs/05-troubleshooting.md) | Common errors and solutions |
| [New Workflows](../docs/06-new-workflows.md) | RAG, Token Profiler, Cost-Quality |
| [Future Improvements](../docs/07-future-improvements.md) | Planned enhancements |
