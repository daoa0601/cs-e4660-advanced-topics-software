"""
SQLite database operations for experiment logging.

Tables:
- runs: Pipeline execution records (includes agentic metadata)
- stages: Individual stage results (includes streaming metrics)
- quality_scores: Quality evaluation results
"""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import DB_PATH

# Global lock for thread-safe database writes
_db_lock = threading.Lock()


def get_connection() -> sqlite3.Connection:
    """Get a database connection, creating the file if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)  # Longer timeout for concurrent access
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Main runs table - pipeline-level data with agentic metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            workflow TEXT NOT NULL,
            pipeline TEXT NOT NULL,
            pipeline_type TEXT DEFAULT 'linear',
            model TEXT NOT NULL,
            num_stages INTEGER,
            total_input_tokens INTEGER,
            total_output_tokens INTEGER,
            total_cost FLOAT,
            total_latency_ms INTEGER,
            final_output TEXT,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            -- Agentic metadata
            iterations INTEGER DEFAULT 1,
            turns INTEGER DEFAULT 1,
            termination_reason TEXT,
            -- Streaming metrics (averages)
            avg_ttft_ms FLOAT,
            -- Multi-turn context tracking (JSON array)
            context_tokens_by_turn TEXT
        )
    """)
    
    # Stages table - per-stage cost attribution with streaming
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL REFERENCES runs(id),
            stage_order INTEGER NOT NULL,
            stage_name TEXT NOT NULL,
            stage_type TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cost FLOAT,
            latency_ms INTEGER,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            -- Loop/turn metadata
            iteration INTEGER,
            turn INTEGER,
            -- Streaming metrics
            time_to_first_token_ms INTEGER,
            tokens_per_second FLOAT
        )
    """)
    
    # Quality scores table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL UNIQUE REFERENCES runs(id),
            response_length INTEGER,
            word_count INTEGER,
            sentence_count INTEGER,
            avg_sentence_length FLOAT,
            has_structure BOOLEAN,
            vocabulary_richness FLOAT,
            relevance_score FLOAT,
            completeness_score FLOAT,
            clarity_score FLOAT,
            automated_score FLOAT,
            llm_score FLOAT,
            combined_score FLOAT,
            evaluation_cost FLOAT DEFAULT 0
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_workflow_model ON runs(workflow, model)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_pipeline_type ON runs(pipeline_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stages_run_id ON stages(run_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stages_stage_type ON stages(stage_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_run_id ON quality_scores(run_id)")
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at: {DB_PATH}")


def log_run(
    workflow: str,
    pipeline: str,
    model: str,
    num_stages: int,
    total_input_tokens: int,
    total_output_tokens: int,
    total_cost: float,
    total_latency_ms: int,
    final_output: str = "",
    success: bool = True,
    error_message: Optional[str] = None,
    # Agentic metadata
    pipeline_type: str = "linear",
    iterations: int = 1,
    turns: int = 1,
    termination_reason: Optional[str] = None,
    avg_ttft_ms: Optional[float] = None,
    context_tokens_by_turn: Optional[str] = None,
) -> int:
    """Log a pipeline run to the database (thread-safe)."""
    with _db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO runs (
                workflow, pipeline, pipeline_type, model, num_stages,
                total_input_tokens, total_output_tokens,
                total_cost, total_latency_ms, final_output,
                success, error_message,
                iterations, turns, termination_reason,
                avg_ttft_ms, context_tokens_by_turn
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow, pipeline, pipeline_type, model, num_stages,
            total_input_tokens, total_output_tokens,
            total_cost, total_latency_ms, final_output[:2000] if final_output else "",
            success, error_message,
            iterations, turns, termination_reason,
            avg_ttft_ms, context_tokens_by_turn
        ))
        
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return run_id


def log_stage(
    run_id: int,
    stage_order: int,
    stage_name: str,
    stage_type: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    latency_ms: int,
    success: bool = True,
    error_message: Optional[str] = None,
    iteration: Optional[int] = None,
    turn: Optional[int] = None,
    time_to_first_token_ms: Optional[int] = None,
    tokens_per_second: Optional[float] = None,
) -> int:
    """Log a pipeline stage result (thread-safe)."""
    with _db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO stages (
                run_id, stage_order, stage_name, stage_type, model,
                input_tokens, output_tokens, cost, latency_ms,
                success, error_message,
                iteration, turn,
                time_to_first_token_ms, tokens_per_second
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, stage_order, stage_name, stage_type, model,
            input_tokens, output_tokens, cost, latency_ms,
            success, error_message,
            iteration, turn,
            time_to_first_token_ms, tokens_per_second
        ))
        
        stage_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return stage_id


def log_quality_score(
    run_id: int,
    response_length: int,
    word_count: int,
    sentence_count: int,
    avg_sentence_length: float,
    has_structure: bool,
    vocabulary_richness: float,
    automated_score: float,
    relevance_score: Optional[float] = None,
    completeness_score: Optional[float] = None,
    clarity_score: Optional[float] = None,
    llm_score: Optional[float] = None,
    combined_score: Optional[float] = None,
    evaluation_cost: float = 0,
) -> int:
    """Log quality evaluation results (thread-safe)."""
    with _db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO quality_scores (
                run_id, response_length, word_count, sentence_count,
                avg_sentence_length, has_structure, vocabulary_richness,
                relevance_score, completeness_score, clarity_score,
                automated_score, llm_score, combined_score, evaluation_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, response_length, word_count, sentence_count,
            avg_sentence_length, has_structure, vocabulary_richness,
            relevance_score, completeness_score, clarity_score,
            automated_score, llm_score, combined_score, evaluation_cost
        ))
        
        score_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return score_id


# =============================================================================
# Query Functions
# =============================================================================

def get_runs(
    workflow: Optional[str] = None,
    pipeline: Optional[str] = None,
    pipeline_type: Optional[str] = None,
    model: Optional[str] = None,
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
        query += " AND model LIKE ?"
        params.append(f"%{model}%")
    
    if success_only:
        query += " AND success = TRUE"
    
    query += " ORDER BY timestamp DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df


def get_stages(run_id: Optional[int] = None, stage_type: Optional[str] = None) -> pd.DataFrame:
    """Retrieve stages from the database."""
    conn = get_connection()
    
    query = "SELECT * FROM stages WHERE 1=1"
    params = []
    
    if run_id:
        query += " AND run_id = ?"
        params.append(run_id)
    
    if stage_type:
        query += " AND stage_type = ?"
        params.append(stage_type)
    
    query += " ORDER BY run_id, stage_order"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_quality_scores(run_id: Optional[int] = None) -> pd.DataFrame:
    """Retrieve quality scores from the database."""
    conn = get_connection()
    
    if run_id:
        query = "SELECT * FROM quality_scores WHERE run_id = ?"
        df = pd.read_sql_query(query, conn, params=[run_id])
    else:
        query = "SELECT * FROM quality_scores"
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df


def get_runs_with_quality() -> pd.DataFrame:
    """Get runs joined with quality scores."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.*,
            q.automated_score,
            q.llm_score,
            q.combined_score,
            q.evaluation_cost
        FROM runs r
        LEFT JOIN quality_scores q ON r.id = q.run_id
        WHERE r.success = TRUE
        ORDER BY r.timestamp DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# =============================================================================
# Summary Functions
# =============================================================================

def get_pipeline_summary() -> pd.DataFrame:
    """Get summary statistics grouped by pipeline and model."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.workflow,
            r.pipeline,
            r.pipeline_type,
            r.model,
            COUNT(*) as run_count,
            AVG(r.total_cost) as mean_cost,
            AVG(r.total_input_tokens) as mean_input_tokens,
            AVG(r.total_output_tokens) as mean_output_tokens,
            AVG(r.total_latency_ms) as mean_latency_ms,
            AVG(r.num_stages) as avg_stages,
            AVG(r.iterations) as avg_iterations,
            AVG(r.turns) as avg_turns,
            AVG(r.avg_ttft_ms) as mean_ttft_ms,
            AVG(q.combined_score) as mean_quality_score
        FROM runs r
        LEFT JOIN quality_scores q ON r.id = q.run_id
        WHERE r.success = TRUE
        GROUP BY r.workflow, r.pipeline, r.pipeline_type, r.model
        ORDER BY r.workflow, r.pipeline, r.model
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_stage_summary() -> pd.DataFrame:
    """Get summary statistics grouped by stage type."""
    conn = get_connection()
    
    query = """
        SELECT 
            s.stage_type,
            s.model,
            COUNT(*) as count,
            AVG(s.cost) as avg_cost,
            SUM(s.cost) as total_cost,
            AVG(s.input_tokens) as avg_input_tokens,
            AVG(s.output_tokens) as avg_output_tokens,
            AVG(s.latency_ms) as avg_latency_ms,
            AVG(s.time_to_first_token_ms) as avg_ttft_ms,
            AVG(s.tokens_per_second) as avg_throughput
        FROM stages s
        JOIN runs r ON s.run_id = r.id
        WHERE r.success = TRUE AND s.success = TRUE
        GROUP BY s.stage_type, s.model
        ORDER BY s.stage_type, s.model
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_cost_by_stage_type(workflow: Optional[str] = None) -> pd.DataFrame:
    """Get cost breakdown by stage type."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.workflow,
            r.pipeline,
            r.pipeline_type,
            s.stage_type,
            r.model,
            SUM(s.cost) as total_cost,
            AVG(s.cost) as avg_cost,
            COUNT(*) as count
        FROM stages s
        JOIN runs r ON s.run_id = r.id
        WHERE r.success = TRUE AND s.success = TRUE
    """
    params = []
    
    if workflow:
        query += " AND r.workflow = ?"
        params.append(workflow)
    
    query += " GROUP BY r.workflow, r.pipeline, r.pipeline_type, s.stage_type, r.model"
    query += " ORDER BY r.workflow, r.pipeline, s.stage_type, r.model"
    
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df


def get_cost_by_model() -> pd.DataFrame:
    """Get cost breakdown by model across all stages."""
    conn = get_connection()
    
    query = """
        SELECT 
            s.model,
            COUNT(*) as stage_count,
            SUM(s.cost) as total_cost,
            AVG(s.cost) as avg_cost,
            AVG(s.latency_ms) as avg_latency_ms,
            AVG(s.time_to_first_token_ms) as avg_ttft_ms
        FROM stages s
        JOIN runs r ON s.run_id = r.id
        WHERE r.success = TRUE AND s.success = TRUE
        GROUP BY s.model
        ORDER BY total_cost DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_iteration_analysis() -> pd.DataFrame:
    """Analyze cost by iteration count for agentic pipelines."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.pipeline,
            r.pipeline_type,
            r.iterations,
            r.termination_reason,
            COUNT(*) as run_count,
            AVG(r.total_cost) as avg_cost,
            AVG(r.num_stages) as avg_stages
        FROM runs r
        WHERE r.success = TRUE AND r.pipeline_type != 'linear'
        GROUP BY r.pipeline, r.pipeline_type, r.iterations, r.termination_reason
        ORDER BY r.pipeline, r.iterations
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_context_growth_analysis() -> pd.DataFrame:
    """Analyze context token growth in multi-turn conversations."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.pipeline,
            r.turns,
            s.turn,
            AVG(s.input_tokens) as avg_context_tokens,
            AVG(s.cost) as avg_cost_per_turn
        FROM runs r
        JOIN stages s ON r.id = s.run_id
        WHERE r.success = TRUE AND r.pipeline_type = 'multiturn'
        GROUP BY r.pipeline, r.turns, s.turn
        ORDER BY r.pipeline, s.turn
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
            s.stage_type,
            s.model,
            COUNT(*) as count,
            AVG(s.time_to_first_token_ms) as avg_ttft_ms,
            MIN(s.time_to_first_token_ms) as min_ttft_ms,
            MAX(s.time_to_first_token_ms) as max_ttft_ms,
            AVG(s.tokens_per_second) as avg_throughput,
            AVG(s.latency_ms) as avg_total_latency_ms
        FROM stages s
        JOIN runs r ON s.run_id = r.id
        WHERE s.time_to_first_token_ms IS NOT NULL
        GROUP BY r.pipeline, s.stage_type, s.model
        ORDER BY r.pipeline, s.stage_type
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# =============================================================================
# Utility Functions
# =============================================================================

def get_run_count() -> int:
    """Get total number of runs in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM runs")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def clear_all():
    """Clear all data from the database (use with caution)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quality_scores")
    cursor.execute("DELETE FROM stages")
    cursor.execute("DELETE FROM runs")
    conn.commit()
    conn.close()
    print("All data cleared from database.")


if __name__ == "__main__":
    init_db()
    print(f"\nTotal runs in database: {get_run_count()}")
