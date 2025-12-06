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
- All workflows (verbosity, context, react, multiturn, self_correcting, document)
- Both models (Flash & Pro)
- 20 iterations each
- 16 parallel workers
- Streaming metrics (TTFT)
- LLM quality evaluation
- A/B testing

### Individual Workflows

```bash
# Run specific workflow
python3 -m src.experiment --workflow react --model flash --iterations 10

# With streaming metrics
python3 -m src.experiment --workflow verbosity --model pro --streaming

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

---

## Project Structure

```
project-demo/
├── src/
│   ├── experiment.py          # Main CLI entry point
│   ├── session.py             # Session management
│   ├── clients/               # LLM client (google-genai SDK)
│   ├── config/                # Model configs, prompts
│   ├── pricing/               # Tiered pricing (200K threshold)
│   └── experiments/           # Domain & verified experiments
├── notebooks/
│   ├── analysis.ipynb         # Jupyter analysis
│   ├── generate_report.py     # Auto-generate figures
│   └── flash_vs_pro_analysis.py
├── figures/                   # Generated visualizations
├── sessions/                  # Isolated experiment runs
└── data/                      # Default database
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

---

## Documentation

See [LLM_Cost_Decomposition_Platform_Report.md](../LLM_Cost_Decomposition_Platform_Report.md) for detailed findings.
