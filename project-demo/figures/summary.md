# Experiment Results Summary

Generated: 2025-12-06 14:47

## Overview

| Metric | Value |
|--------|-------|
| Total Runs | 766 |
| Total Cost | $8.2187 |

## Model Comparison

| Model | Runs | Total Cost | Avg Cost |
|-------|------|------------|----------|
| Flash | 410 | $2.1969 | $0.005358 |
| Pro | 356 | $6.0218 | $0.016915 |

**Cost Ratio**: Pro costs 3.2x more than Flash

## Quality Comparison

| Model | Avg Quality |
|-------|-------------|
| Flash | 82.26 |
| Pro | 84.61 |

**Quality Difference**: Pro scores +2.35 points higher

## Figures Generated

1. `01_cost_by_model.png` - Overall cost comparison
2. `02_cost_by_pipeline.png` - Cost by pipeline
3. `03_quality_by_model.png` - Quality comparison
4. `04_cost_quality_scatter.png` - Cost vs quality
5. `05_stage_cost_distribution.png` - Stage costs
6. `06_pro_vs_flash_advantage.png` - Pro advantage by pipeline
7. `07_verified_accuracy.png` - Accuracy on verified problems (if available)

## Verified Experiments (Ground Truth)

These tests use problems with known correct answers for objective accuracy.

| Difficulty | Flash Accuracy | Pro Accuracy | Pro Advantage |
|------------|---------------|--------------|---------------|
| All | 95.0% | 100.0% | +5.3% |
| **Hard** | 60.0% | 80.0% | +33.3% |

> **Key Finding**: Pro's advantage increases on harder problems, justifying its premium for complex reasoning tasks.
