# LLM Cost Decomposition Platform

> Granular cost analysis for multi-stage LLM pipelines

**Aalto University** — Advanced Topics in Software Systems  
**Author**: Anh Dao | December 2025

---

## Overview

A platform that answers: **"Where does money go in LLM pipelines?"**

Modern LLM applications use complex multi-stage pipelines—agentic workflows, multi-model architectures, self-correcting systems—but current cost tracking only provides aggregate metrics. This platform provides:

- **Per-stage cost attribution** for multi-step workflows
- **Flash vs Pro model comparison** with ground truth verification
- **Agentic loop cost analysis** (ReAct, self-correcting)
- **Session management** for reproducible experiments

---

## Project Evolution

| Version | Description | Key Features |
|---------|-------------|--------------|
| **MVP** | Initial prototype | Basic cost tracking, vertexai SDK |
| **Demo v1** | Enhanced platform | Streaming metrics, parallel execution, quality evaluation |
| **Demo v2.0** | Current version | google-genai SDK, tiered pricing, session management, verified experiments |

### v2.0 Enhancements

- **SDK Migration**: `vertexai` → `google-genai` with ADC authentication
- **Tiered Pricing**: Long-context rates (>200K tokens = 2x)
- **Session Management**: Isolated experiment runs with separate databases
- **Ground Truth Verification**: 30 problems with known correct answers
- **Automated Report Generation**: 7 figures + summary in one command

---

## Latest Results (v2.0 Full Suite)

| Metric | Value |
|--------|-------|
| Pipeline Runs | **1,545** |
| Stage Executions | **3,599** |
| Total Cost | **$16.72** |

### Model Comparison

| Model | Avg Cost/Run | Avg Quality |
|-------|-------------|-------------|
| Flash | $0.0052 | 82.86 |
| Pro | $0.0170 | 84.45 |

**Cost Ratio**: Pro costs **3.3x** more than Flash  
**Quality Difference**: Pro scores **+1.59** points higher

### Verified Accuracy (Ground Truth)

| Difficulty | Flash | Pro | Pro Advantage |
|------------|-------|-----|---------------|
| All | 95% | 100% | +5.3% |
| **Hard** | 60% | 80% | **+33.3%** |

> **Key Finding**: Pro's advantage increases dramatically on hard problems, justifying its premium for complex reasoning tasks.

---

## Quick Start

```bash
cd project-demo
pip install -r requirements.txt
cp .env.example .env  # Add your GCP_PROJECT_ID

# Create a new session (keeps runs isolated)
python3 -m src.session new "my_experiment"

# Run full experiment suite
python3 -m src.experiment --full-experiment

# Generate report with figures
python3 notebooks/generate_report.py
```

---

## Project Structure

```
├── project-demo/          # Current implementation (v2.0)
│   ├── src/               # Core modules (genai SDK, tiered pricing)
│   ├── notebooks/         # Analysis & report generation
│   ├── sessions/          # Isolated experiment runs
│   └── figures/           # Generated visualizations
├── project-mvp/           # Original prototype (archived)
├── docs/                   # Detailed documentation
└── LLM_Cost_Decomposition_Platform_Report.md
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Project Report](LLM_Cost_Decomposition_Platform_Report.md) | Full findings and methodology |
| [Demo README](project-demo/README.md) | How to run experiments |
| [Architecture](docs/01-architecture.md) | System design |
| [Recommendations](docs/04-recommendations.md) | When to use Pro vs Flash |

---

## Key Commands

```bash
# Session management
python3 -m src.session new "name"     # Create isolated session
python3 -m src.session list            # List all sessions

# Experiments
python3 -m src.experiment --full-experiment
python3 -m src.experiment --workflow react --model flash

# Reports
python3 notebooks/generate_report.py
```

---

**v2.0** | December 2025 | Total Experiment Cost: $16.72
