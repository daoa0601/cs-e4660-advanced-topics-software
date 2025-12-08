# Experiment Reports

This directory contains all experiment reports and generated figures.

## Report Index

| Version | Phase | Date | Description |
|---------|-------|------|-------------|
| [v1.0](mvp-v1.0/) | MVP | Dec 2024 | Initial baseline experiments |
| [v2.0](demo-v2.0/) | Demo | Dec 2024 | Streaming, parallel execution, quality evaluation |
| [v2.1](v2.1-template/) | Template | - | Template for next experiment run |

## Directory Structure

```
reports/
├── mvp-v1.0/              # MVP phase experiments
│   └── mvp_report.pdf     # Full report document
├── demo-v2.0/             # Demo phase experiments
│   ├── demo_report.pdf    # Full report document
│   ├── summary.md         # Key metrics summary
│   └── figures/           # Generated visualizations
│       ├── 01_cost_by_model.png
│       ├── 02_cost_by_pipeline.png
│       └── ...
└── v2.1-template/         # Template for next run
    ├── experiment-config.json
    └── README.md
```

## Generating New Reports

```bash
# Generate report to default location (reports/latest/)
python3 notebooks/generate_report.py

# Generate to specific directory
python3 notebooks/generate_report.py --output-dir reports/v2.1-my-experiment/
```

## Report Contents

Each versioned report directory should contain:
- `*_report.pdf` - Full report document (manual export from analysis)
- `summary.md` - Auto-generated key metrics summary
- `figures/` - All visualization PNGs
- `experiment-config.json` (optional) - Experiment configuration used

## Backward Compatibility

The `figures/` symlink in project root points to `reports/demo-v2.0/figures/` for backward compatibility with existing scripts and documentation.
