# Troubleshooting Guide

**Version:** 3.0  
**Last Updated:** December 2025

Common issues and solutions for the LLM Cost Decomposition Platform.

---

## 1. API Errors

### Authentication Issues

**Error:** `google.auth.exceptions.DefaultCredentialsError`

**Solution:**
```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Or set credentials file
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Quota Exceeded

**Error:** `ResourceExhausted: 429 Quota exceeded`

**Solution:**
- Reduce `--workers` count for parallel execution
- Add delay between calls with `--delay 2.0`
- Check your GCP quota limits in the Cloud Console

### Region Issues

**Error:** `Location X is not supported`

**Solution:**
Update your `.env` file:
```bash
GCP_REGION=us-central1  # Or your preferred region
```

Available regions: `us-central1`, `us-east1`, `europe-west1`, `asia-east1`

### Model Not Found

**Error:** `Model gemini-X not found`

**Solution:**
- Ensure you have access to the Gemini 2.5 models
- Check model name spelling in `--model` flag
- Verify your GCP project has the Vertex AI API enabled

---

## 2. Database Issues

### Connection Failed

**Error:** `sqlite3.OperationalError: unable to open database file`

**Solution:**
```bash
# Create data directory
mkdir -p data

# Check permissions
chmod 755 data

# Verify path in .env
DATABASE_PATH=data/experiments.db
```

### Schema Mismatch

**Error:** `sqlite3.OperationalError: no such column`

**Solution:**
```bash
# Reset the database (WARNING: deletes all data)
python3 -m src.experiment --reset

# Or backup and recreate
mv data/experiments.db data/experiments.db.backup
python3 -m src.experiment --health-check
```

### Database Locked

**Error:** `sqlite3.OperationalError: database is locked`

**Solution:**
- Close other processes accessing the database
- Reduce `--workers` count
- Use session management to isolate experiments:
  ```bash
  python3 -m src.session new "my_experiment"
  ```

---

## 3. Configuration Problems

### Missing Environment Variables

**Error:** `KeyError: 'GCP_PROJECT_ID'`

**Solution:**
```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env
```

Required variables:
```
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
```

### Pricing Data Not Found

**Error:** `FileNotFoundError: pricing config not found`

**Solution:**
Ensure pricing config exists:
```bash
ls src/config/pricing.yaml  # or .json
```

### Invalid Workflow

**Error:** `Invalid workflow: X`

**Solution:**
```bash
# List available workflows
python3 -m src.experiment --list-pipelines

# Valid workflows:
# verbosity, context, react, multiturn, self_correcting, document, rag
# Analysis workflows: token_profile, cost_quality
```

---

## 4. Performance Issues

### Slow Experiments

**Symptoms:** Experiments taking longer than expected

**Solutions:**
1. Enable parallel execution:
   ```bash
   python3 -m src.experiment --parallel --workers 8
   ```

2. Reduce iterations for testing:
   ```bash
   python3 -m src.experiment --workflow react --iterations 5
   ```

3. Use Flash model for faster iteration:
   ```bash
   python3 -m src.experiment --model flash
   ```

### High Memory Usage

**Symptoms:** Process killed, memory errors

**Solutions:**
1. Reduce worker count:
   ```bash
   python3 -m src.experiment --workers 4
   ```

2. Run workflows sequentially:
   ```bash
   python3 -m src.experiment --workflow verbosity
   python3 -m src.experiment --workflow context
   ```

3. Clear cache between runs:
   ```python
   from src.visualization import clear_cache
   clear_cache()
   ```

### Streaming Timeouts

**Error:** `Timeout waiting for streaming response`

**Solution:**
- Disable streaming for problematic workflows:
  ```bash
  python3 -m src.experiment --workflow react  # Without --streaming
  ```
- Increase timeout in client configuration

---

## 5. Visualization Issues

### Kaleido Not Installed

**Warning:** `Figures saved as HTML (install kaleido for PNG)`

**Solution:**
```bash
pip install kaleido
```

### Empty Figures

**Symptoms:** Charts showing no data

**Solutions:**
1. Check if data exists:
   ```bash
   python3 -m src.experiment --summary
   ```

2. Ensure experiments completed:
   ```bash
   python3 -m src.experiment --health-check
   ```

3. Check quality scores:
   ```python
   from src.db import get_quality_scores
   print(get_quality_scores())
   ```

---

## 6. FAQ

### How do I start fresh?

```bash
# Create new session (recommended)
python3 -m src.session new "fresh_start"

# Or reset default database
python3 -m src.experiment --reset
```

### How do I export results?

```bash
# Generate figures
python3 notebooks/generate_report.py

# Results in figures/ directory:
# - PNG charts
# - summary.md with key metrics
```

### How do I compare different runs?

Use session management:
```bash
# Create sessions for each experiment
python3 -m src.session new "baseline"
python3 -m src.experiment --full-suite

python3 -m src.session new "with_cot"
python3 -m src.experiment --full-suite

# List sessions
python3 -m src.session list
```

### What's the difference between Flash and Pro?

| Aspect | Flash | Pro |
|--------|-------|-----|
| Speed | Faster | Slower |
| Cost | ~7x cheaper | More expensive |
| Quality | Good for simple tasks | Better for complex reasoning |
| Use Case | High volume, cost-sensitive | Complex, quality-critical |

### How do I add custom pipelines?

See [03-pipelines.md](03-pipelines.md) for pipeline architecture and extension guide.

---

## Getting Help

1. Check the health of your setup:
   ```bash
   python3 -m src.experiment --health-check
   ```

2. Enable debug logging:
   ```bash
   python3 -m src.experiment --workflow X --log-level DEBUG
   ```

3. Review the main documentation:
   - [01-architecture.md](01-architecture.md)
   - [02-experiments.md](02-experiments.md)
   - [03-pipelines.md](03-pipelines.md)
   - [04-recommendations.md](04-recommendations.md)
   - [06-new-workflows.md](06-new-workflows.md)

