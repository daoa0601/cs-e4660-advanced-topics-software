# LLM Cost Decomposition Platform

> Granular cost analysis for multi-stage LLM pipelines

**Aalto University** — Advanced Topics in Software Systems  
**Author**: Anh Dao | December 2025

## What is this?

A platform that answers: **"Where does money go in LLM pipelines?"**

- Per-stage cost attribution for complex workflows
- Flash vs Pro model comparison with ground truth verification
- Agentic loop cost analysis (ReAct, self-correcting)
- A/B testing for prompt optimization

## Key Findings

| Finding | Impact |
|---------|--------|
| Flash vs Pro | Flash is **3x cheaper** with 2-3 quality point difference |
| Hybrid pipelines | 60% cost reduction, 96% quality |
| Prompt engineering | Concise = **25x cheaper** than detailed |
| Pro advantage | **+33% accuracy** on hard reasoning tasks |

## Quick Start

```bash
cd project-demo
pip install -r requirements.txt

# Run full experiment suite
python3 -m src.experiment --full-experiment

# Generate report with figures
python3 notebooks/generate_report.py
```

## Structure

```
├── project-demo/          # Main implementation (google-genai SDK)
│   ├── src/               # Core modules
│   ├── notebooks/         # Analysis & report generation
│   └── figures/           # Generated visualizations
├── project-mvp/           # Original prototype (vertexai SDK)
├── docs/                   # Detailed documentation
└── LLM_Cost_Decomposition_Platform_Report.md
```

## Documentation

- [Project Report](LLM_Cost_Decomposition_Platform_Report.md) - Full findings
- [Demo README](project-demo/README.md) - How to run experiments
- [Architecture](docs/01-architecture.md) - System design
- [Recommendations](docs/04-recommendations.md) - When to use Pro vs Flash

---

**Total Experiment Cost**: $14.47 | **Pipeline Runs**: 1,327
