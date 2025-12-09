"""
Health check and cost estimation utilities.

Contains:
- run_health_check(): System health validation
- estimate_experiment_cost(): Pre-execution cost estimation
- print_cost_estimate(): Formatted cost estimate output
"""

from ..config import get_model_id
from ..clients import test_connection, test_streaming
from ..cost_calculator import calculate_cost, format_cost
from ..db import init_db
from ..pipeline import list_pipelines


def run_health_check() -> bool:
    """
    Check system health: database, API connectivity, and configuration.

    Returns:
        True if all checks pass, False otherwise
    """
    print("\n" + "="*60)
    print("System Health Check")
    print("="*60 + "\n")

    all_passed = True

    # 1. Check configuration
    print("1. Configuration")
    try:
        from ..config import GCP_PROJECT_ID, GCP_REGION, DB_PATH
        if GCP_PROJECT_ID:
            print(f"   - GCP_PROJECT_ID: {GCP_PROJECT_ID}")
        else:
            print("   x GCP_PROJECT_ID: Not set")
            all_passed = False
        print(f"   - GCP_REGION: {GCP_REGION}")
        print(f"   - DB_PATH: {DB_PATH}")
    except Exception as e:
        print(f"   x Configuration error: {e}")
        all_passed = False

    # 2. Check database
    print("\n2. Database")
    try:
        init_db()
        from ..db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM runs")
        run_count = cursor.fetchone()[0]
        conn.close()
        print(f"   - Database accessible ({run_count} existing runs)")
    except Exception as e:
        print(f"   x Database error: {e}")
        all_passed = False

    # 3. Check API connectivity
    print("\n3. API Connectivity")
    try:
        if test_connection():
            print("   - Gemini API connection successful")
        else:
            print("   x Gemini API connection failed")
            all_passed = False
    except Exception as e:
        print(f"   x API error: {e}")
        all_passed = False

    # 4. Check streaming
    print("\n4. Streaming API")
    try:
        if test_streaming():
            print("   - Streaming API functional")
        else:
            print("   ~ Streaming API unavailable (non-critical)")
    except Exception as e:
        print(f"   ~ Streaming check failed: {e} (non-critical)")

    # 5. Check pipelines
    print("\n5. Pipeline Registry")
    try:
        pipelines = list_pipelines()
        print(f"   - {len(pipelines)} pipelines registered")
    except Exception as e:
        print(f"   x Pipeline registry error: {e}")
        all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("Health Check: PASSED")
    else:
        print("Health Check: FAILED")
    print("="*60 + "\n")

    return all_passed


def estimate_experiment_cost(
    workflow: str,
    model: str,
    iterations: int,
) -> dict:
    """
    Estimate the cost of running an experiment before execution.

    Args:
        workflow: Workflow name
        model: Model identifier
        iterations: Number of iterations

    Returns:
        Dict with cost estimates
    """
    # Estimated tokens per workflow (based on typical usage)
    WORKFLOW_ESTIMATES = {
        "verbosity": {
            "variants": 3,
            "avg_input_tokens": 500,
            "avg_output_tokens": 800,
        },
        "context": {
            "variants": 2,
            "avg_input_tokens": 2000,
            "avg_output_tokens": 500,
        },
        "react": {
            "variants": 2,
            "avg_input_tokens": 1500,
            "avg_output_tokens": 1200,
            "avg_iterations": 3,  # ReAct loops
        },
        "multiturn": {
            "variants": 2,
            "avg_input_tokens": 800,
            "avg_output_tokens": 600,
            "avg_turns": 4,  # Average turns
        },
        "self_correcting": {
            "variants": 2,
            "avg_input_tokens": 1000,
            "avg_output_tokens": 1500,
            "avg_retries": 2,
        },
        "document": {
            "variants": 4,
            "avg_input_tokens": 3000,
            "avg_output_tokens": 1000,
        },
        "rag": {
            "variants": 3,
            "avg_input_tokens": 2000,
            "avg_output_tokens": 1000,
        },
    }

    if workflow not in WORKFLOW_ESTIMATES:
        return {"error": f"Unknown workflow: {workflow}"}

    est = WORKFLOW_ESTIMATES[workflow]
    variants = est["variants"]
    input_tokens = est["avg_input_tokens"]
    output_tokens = est["avg_output_tokens"]

    # Adjust for multi-step workflows
    multiplier = 1
    if "avg_iterations" in est:
        multiplier = est["avg_iterations"]
    elif "avg_turns" in est:
        multiplier = est["avg_turns"]
    elif "avg_retries" in est:
        multiplier = est["avg_retries"]

    # Calculate per-iteration cost
    per_iteration_cost = calculate_cost(
        input_tokens * multiplier,
        output_tokens * multiplier,
        model
    )

    # Total estimates
    total_iterations = iterations * variants
    total_cost = per_iteration_cost * total_iterations
    min_cost = total_cost * 0.7  # -30% variance
    max_cost = total_cost * 1.5  # +50% variance

    return {
        "workflow": workflow,
        "model": get_model_id(model),
        "iterations": iterations,
        "variants": variants,
        "total_api_calls": total_iterations,
        "estimated_cost": total_cost,
        "cost_range": (min_cost, max_cost),
        "per_iteration": per_iteration_cost,
    }


def print_cost_estimate(workflow: str, model: str, iterations: int):
    """Print formatted cost estimate."""
    est = estimate_experiment_cost(workflow, model, iterations)

    if "error" in est:
        print(f"Error: {est['error']}")
        return

    print("\n" + "="*60)
    print("Cost Estimate")
    print("="*60)
    print(f"  Workflow:        {est['workflow']}")
    print(f"  Model:           {est['model']}")
    print(f"  Iterations:      {est['iterations']} x {est['variants']} variants")
    print(f"  Total API calls: {est['total_api_calls']}")
    print(f"  Per iteration:   {format_cost(est['per_iteration'])}")
    print("-"*60)
    print(f"  Estimated cost:  {format_cost(est['estimated_cost'])}")
    print(f"  Expected range:  {format_cost(est['cost_range'][0])} - {format_cost(est['cost_range'][1])}")
    print("="*60)
    print("\nNote: Actual costs may vary based on response length and complexity.")
    print("Use --llm-eval to add ~$0.01-0.05 per iteration for quality scoring.\n")
