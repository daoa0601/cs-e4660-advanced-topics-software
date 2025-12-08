"""
Database schema definitions.

Tables:
- runs: Pipeline execution records with agentic metadata and prompt variants
- stages: Individual stage results with streaming metrics
- quality_scores: Quality evaluation results
- ab_tests: A/B test experiment tracking
"""

from .connection import get_connection


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Main runs table - pipeline-level data with agentic metadata and prompt variants
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
            avg_ttft_ms FLOAT,
            context_tokens_by_turn TEXT,
            -- A/B testing: prompt variant tracking
            prompt_variant TEXT,
            ab_test_name TEXT
        )
    """)
    
    # Stages table - per-stage results with streaming metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
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
            -- Loop/turn tracking
            iteration INTEGER,
            turn INTEGER,
            -- Streaming metrics
            time_to_first_token_ms INTEGER,
            tokens_per_second FLOAT,
            -- A/B testing: per-stage prompt variant
            prompt_variant TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)
    
    # Quality scores table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
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
            evaluation_cost FLOAT DEFAULT 0,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)
    
    # A/B test tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            test_name TEXT NOT NULL,
            prompt_name TEXT NOT NULL,
            variants TEXT NOT NULL,
            iterations_per_variant INTEGER,
            total_runs INTEGER,
            status TEXT DEFAULT 'running',
            description TEXT
        )
    """)
    
    # Create indexes for common queries
    # Single-column indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_workflow ON runs(workflow)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_pipeline ON runs(pipeline)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_model ON runs(model)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_prompt_variant ON runs(prompt_variant)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_ab_test ON runs(ab_test_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stages_run_id ON stages(run_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stages_stage_type ON stages(stage_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_run_id ON quality_scores(run_id)")

    # Compound indexes for common query patterns
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_workflow_model ON runs(workflow, model)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stages_run_turn ON stages(run_id, turn)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON runs(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stages_run_iteration ON stages(run_id, iteration)")
    
    conn.commit()
    conn.close()


def clear_all():
    """Clear all data from the database (for reset)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM quality_scores")
    cursor.execute("DELETE FROM stages")
    cursor.execute("DELETE FROM runs")
    cursor.execute("DELETE FROM ab_tests")
    
    conn.commit()
    conn.close()


def get_table_info() -> dict:
    """Get information about database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    tables = {}
    for table in ["runs", "stages", "quality_scores", "ab_tests"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        tables[table] = {"count": count}
    
    conn.close()
    return tables
