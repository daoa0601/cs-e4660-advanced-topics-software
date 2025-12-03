"""
Database query operations for analysis.
"""

from typing import Optional
import pandas as pd

from .connection import get_connection


def get_runs(
    workflow: Optional[str] = None,
    pipeline: Optional[str] = None,
    pipeline_type: Optional[str] = None,
    model: Optional[str] = None,
    prompt_variant: Optional[str] = None,
    ab_test_name: Optional[str] = None,
    success_only: bool = True,
) -> pd.DataFrame:
    """Retrieve runs from the database as a DataFrame."""
    conn = get_connection()
    
    query = "SELECT * FROM runs WHERE 1=1"
    params = []
    
    if workflow:
        query += " AND workflow = ?"
        params.append(workflow)
    if pipeline:
        query += " AND pipeline = ?"
        params.append(pipeline)
    if pipeline_type:
        query += " AND pipeline_type = ?"
        params.append(pipeline_type)
    if model:
        query += " AND model = ?"
        params.append(model)
    if prompt_variant:
        query += " AND prompt_variant = ?"
        params.append(prompt_variant)
    if ab_test_name:
        query += " AND ab_test_name = ?"
        params.append(ab_test_name)
    if success_only:
        query += " AND success = 1"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_stages(run_id: Optional[int] = None) -> pd.DataFrame:
    """Retrieve stages from the database."""
    conn = get_connection()
    
    if run_id:
        query = "SELECT * FROM stages WHERE run_id = ?"
        df = pd.read_sql_query(query, conn, params=[run_id])
    else:
        df = pd.read_sql_query("SELECT * FROM stages", conn)
    
    conn.close()
    return df


def get_quality_scores(run_id: Optional[int] = None) -> pd.DataFrame:
    """Retrieve quality scores from the database."""
    conn = get_connection()
    
    if run_id:
        query = "SELECT * FROM quality_scores WHERE run_id = ?"
        df = pd.read_sql_query(query, conn, params=[run_id])
    else:
        df = pd.read_sql_query("SELECT * FROM quality_scores", conn)
    
    conn.close()
    return df


def get_pipeline_summary() -> pd.DataFrame:
    """Get summary statistics by pipeline."""
    conn = get_connection()
    
    query = """
        SELECT 
            pipeline,
            pipeline_type,
            model,
            COUNT(*) as runs,
            AVG(total_cost) as avg_cost,
            AVG(total_latency_ms) as avg_latency_ms,
            AVG(total_input_tokens) as avg_input_tokens,
            AVG(total_output_tokens) as avg_output_tokens,
            AVG(iterations) as avg_iterations
        FROM runs
        WHERE success = 1
        GROUP BY pipeline, pipeline_type, model
        ORDER BY pipeline, model
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_stage_summary() -> pd.DataFrame:
    """Get summary statistics by stage type."""
    conn = get_connection()
    
    query = """
        SELECT 
            stage_type,
            model,
            COUNT(*) as count,
            AVG(cost) as avg_cost,
            SUM(cost) as total_cost,
            AVG(latency_ms) as avg_latency_ms,
            AVG(input_tokens) as avg_input_tokens,
            AVG(output_tokens) as avg_output_tokens
        FROM stages
        WHERE success = 1
        GROUP BY stage_type, model
        ORDER BY total_cost DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_cost_by_model() -> pd.DataFrame:
    """Get cost breakdown by model."""
    conn = get_connection()
    
    query = """
        SELECT 
            model,
            COUNT(*) as runs,
            SUM(total_cost) as total_cost,
            AVG(total_cost) as avg_cost,
            SUM(total_input_tokens) as total_input_tokens,
            SUM(total_output_tokens) as total_output_tokens
        FROM runs
        WHERE success = 1
        GROUP BY model
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_cost_by_stage_type() -> pd.DataFrame:
    """Get cost breakdown by stage type."""
    conn = get_connection()
    
    query = """
        SELECT 
            stage_type,
            model,
            SUM(cost) as total_cost,
            AVG(cost) as avg_cost,
            COUNT(*) as count
        FROM stages
        WHERE success = 1
        GROUP BY stage_type, model
        ORDER BY total_cost DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_iteration_analysis() -> pd.DataFrame:
    """Analyze iteration patterns for agentic pipelines."""
    conn = get_connection()
    
    query = """
        SELECT 
            pipeline,
            model,
            COUNT(*) as runs,
            AVG(iterations) as avg_iterations,
            MIN(iterations) as min_iterations,
            MAX(iterations) as max_iterations,
            AVG(total_cost) as avg_cost,
            AVG(total_cost / iterations) as cost_per_iteration,
            termination_reason,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY pipeline, model) as termination_pct
        FROM runs
        WHERE success = 1 AND pipeline_type IN ('react', 'self_correcting')
        GROUP BY pipeline, model, termination_reason
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_context_growth_analysis() -> pd.DataFrame:
    """Analyze context growth in multi-turn conversations."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.pipeline,
            r.model,
            s.turn,
            AVG(s.input_tokens) as avg_input_tokens,
            AVG(s.cost) as avg_cost
        FROM stages s
        JOIN runs r ON s.run_id = r.id
        WHERE r.pipeline_type = 'multiturn' AND s.turn IS NOT NULL
        GROUP BY r.pipeline, r.model, s.turn
        ORDER BY r.pipeline, r.model, s.turn
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_streaming_analysis() -> pd.DataFrame:
    """Analyze streaming metrics (TTFT, throughput)."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.pipeline,
            r.model,
            s.stage_type,
            AVG(s.time_to_first_token_ms) as avg_ttft_ms,
            AVG(s.latency_ms) as avg_total_latency_ms,
            AVG(s.tokens_per_second) as avg_throughput,
            COUNT(*) as samples
        FROM stages s
        JOIN runs r ON s.run_id = r.id
        WHERE s.time_to_first_token_ms IS NOT NULL
        GROUP BY r.pipeline, r.model, s.stage_type
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# =============================================================================
# A/B Test Analysis Queries
# =============================================================================

def get_ab_test_summary(test_name: Optional[str] = None) -> pd.DataFrame:
    """Get summary of A/B test results by prompt variant."""
    conn = get_connection()
    
    query = """
        SELECT 
            ab_test_name,
            prompt_variant,
            model,
            COUNT(*) as runs,
            AVG(total_cost) as avg_cost,
            AVG(total_latency_ms) as avg_latency_ms,
            AVG(total_input_tokens) as avg_input_tokens,
            AVG(total_output_tokens) as avg_output_tokens
        FROM runs
        WHERE success = 1 AND ab_test_name IS NOT NULL
    """
    
    params = []
    if test_name:
        query += " AND ab_test_name = ?"
        params.append(test_name)
    
    query += " GROUP BY ab_test_name, prompt_variant, model ORDER BY ab_test_name, avg_cost"
    
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df


def get_ab_test_quality(test_name: Optional[str] = None) -> pd.DataFrame:
    """Get quality metrics by prompt variant for A/B tests."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.ab_test_name,
            r.prompt_variant,
            r.model,
            COUNT(*) as runs,
            AVG(q.automated_score) as avg_automated_score,
            AVG(q.llm_score) as avg_llm_score,
            AVG(q.combined_score) as avg_combined_score,
            AVG(q.response_length) as avg_response_length,
            AVG(q.vocabulary_richness) as avg_vocabulary_richness
        FROM runs r
        JOIN quality_scores q ON r.id = q.run_id
        WHERE r.success = 1 AND r.ab_test_name IS NOT NULL
    """
    
    params = []
    if test_name:
        query += " AND r.ab_test_name = ?"
        params.append(test_name)
    
    query += " GROUP BY r.ab_test_name, r.prompt_variant, r.model ORDER BY r.ab_test_name, avg_combined_score DESC"
    
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df


def get_ab_test_cost_quality_ratio(test_name: Optional[str] = None) -> pd.DataFrame:
    """Get cost-quality ratio by prompt variant."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.ab_test_name,
            r.prompt_variant,
            r.model,
            COUNT(*) as runs,
            AVG(r.total_cost) as avg_cost,
            AVG(q.combined_score) as avg_quality,
            AVG(r.total_cost * 100000 / NULLIF(q.combined_score, 0)) as cost_per_quality_point
        FROM runs r
        JOIN quality_scores q ON r.id = q.run_id
        WHERE r.success = 1 AND r.ab_test_name IS NOT NULL AND q.combined_score > 0
    """
    
    params = []
    if test_name:
        query += " AND r.ab_test_name = ?"
        params.append(test_name)
    
    query += " GROUP BY r.ab_test_name, r.prompt_variant, r.model ORDER BY r.ab_test_name, cost_per_quality_point"
    
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df


def get_variant_comparison(
    prompt_variant_a: str,
    prompt_variant_b: str,
    workflow: Optional[str] = None,
) -> pd.DataFrame:
    """Compare two prompt variants directly."""
    conn = get_connection()
    
    query = """
        SELECT 
            prompt_variant,
            COUNT(*) as runs,
            AVG(total_cost) as avg_cost,
            AVG(total_latency_ms) as avg_latency_ms,
            AVG(total_output_tokens) as avg_output_tokens
        FROM runs
        WHERE success = 1 AND prompt_variant IN (?, ?)
    """
    
    params = [prompt_variant_a, prompt_variant_b]
    
    if workflow:
        query += " AND workflow = ?"
        params.append(workflow)
    
    query += " GROUP BY prompt_variant"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_ab_tests() -> pd.DataFrame:
    """Get list of all A/B tests."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM ab_tests ORDER BY timestamp DESC", conn)
    conn.close()
    return df
