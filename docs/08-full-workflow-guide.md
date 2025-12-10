# Full Experiment Workflow Guide

This guide details the complete process for running the full suite of experiments for the LLM Cost Decomposition Platform, including the necessary data preparation steps for RAG.

## 1. Environment Setup

Ensure your environment is correctly configured before starting.

1.  **Install Dependencies**
    ```bash
    cd project-demo
    pip install -r requirements.txt
    ```

2.  **Configure Environment Variables**
    Ensure your `.env` file is set up with your Google Cloud credentials.
    ```bash
    cp .env.example .env
    # Edit .env to add your GCP_PROJECT_ID and GCP_REGION
    ```

3.  **Authentication**
    If running locally without a service account key file:
    ```bash
    gcloud auth application-default login
    ```

## 2. RAG Data Preparation (Critical Step)

The RAG experiments require a real vector index. You must generate the corpus and build the index **before** running the full suite.

1.  **Generate Academic Corpus**
    This script downloads papers from arXiv and chunks them.
    ```bash
    # Download 50 papers from arXiv
    python3 scripts/generate_academic_corpus.py --source arxiv --papers 50 --output test-docs/arxiv
    ```

2.  **Build FAISS Index**
    This script creates the vector embeddings from the generated corpus.
    ```bash
    # Build the index from the generated compatibility file
    python3 scripts/build_rag_index.py --input test-docs/academic_corpus.jsonl --output data/faiss
    ```

## 3. Session Management

It is highly recommended to run experiments in an isolated session to keep data and results organized.

1.  **Create a New Session**
    ```bash
    python3 -m src.session new "full_run_v1"
    ```
    *All subsequent commands will automatically use this session's database and output directories.*

## 4. Running the Experiments

You can now run the experiments.

### Option A: One-Click Full Run (`--full-experiment`)

For production-quality results with all features enabled:

```bash
python3 -m src.experiment --full-experiment
```

This is the recommended approach for complete experiment runs. All settings are optimized and A/B testing is included.

### Option B: Customizable Full Run (`--full-suite`)

For quick tests or debugging with custom settings:

```bash
# Quick test with fewer iterations
python3 -m src.experiment --full-suite --iterations 5 --parallel --workers 8

# Full run with custom workers
python3 -m src.experiment --full-suite --iterations 20 --parallel --workers 12 --streaming --llm-eval
```

### Comparison: `--full-experiment` vs `--full-suite`

| Feature | `--full-experiment` | `--full-suite` |
|---------|---------------------|----------------|
| **Use case** | One-click production run | Custom/quick testing |
| Iterations | Fixed: 20 | Customizable |
| Workers | Fixed: 16 | Customizable |
| Parallel | Always ON | Via `--parallel` |
| Streaming | Always ON | Via `--streaming` |
| LLM Eval | Always ON | Via `--llm-eval` |
| **A/B Testing** | ✅ Included | ❌ Not included |

> **Tip:** Use `--full-experiment` for final results, `--full-suite` for development/debugging.

### Option C: Specific Workflows
If you only want to test specific components (e.g., just RAG):

```bash
python3 -m src.experiment --workflow rag --model flash --iterations 10
```

## 5. Analysis & Reporting

Once the experiments are complete, generate the analysis report and visualizations.

1.  **Generate Report**
    ```bash
    python3 notebooks/generate_report.py
    ```

2.  **View Results**
    *   **Summary**: Open `sessions/<session_name>/figures/summary.md`
    *   **Plots**: Check the `sessions/<session_name>/figures/` directory for cost and quality charts.

## 6. (Optional) Advanced Analysis

Run these additional analysis workflows that don't incur API costs but provide deeper insights.

```bash
# Analyze token usage patterns
python3 -m src.experiment --workflow token_profile

# Analyze cost-quality Pareto fontier
python3 -m src.experiment --workflow cost_quality --parallel
```
