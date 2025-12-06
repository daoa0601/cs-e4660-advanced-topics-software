# Experiment Results Summary

Generated: 2025-12-06 22:20

## Overview

| Metric | Value |
|--------|-------|
| Total Runs | 1545 |
| Total Cost | $16.7192 |

## Model Comparison

| Model | Runs | Total Cost | Avg Cost |
|-------|------|------------|----------|
| Flash | 809 | $4.1998 | $0.005191 |
| Pro | 736 | $12.5194 | $0.017010 |

**Cost Ratio**: Pro costs 3.3x more than Flash

## Quality Comparison

| Model | Avg Quality |
|-------|-------------|
| Flash | 82.86 |
| Pro | 84.45 |

**Quality Difference**: Pro scores +1.59 points higher

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
