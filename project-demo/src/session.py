#!/usr/bin/env python3
"""
Experiment Session Manager

Create isolated experiment sessions with separate databases and output folders.

Usage:
    # Create a new session
    python -m src.session new "baseline_flash_vs_pro"
    
    # List sessions
    python -m src.session list
    
    # Switch to a session
    python -m src.session use "baseline_flash_vs_pro"
    
    # Run experiments in current session
    python -m src.experiment --full-experiment
    
    # Generate report for current session
    python notebooks/generate_report.py
    
    # Archive current session and start fresh
    python -m src.session archive
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

# Session config file
SESSION_DIR = Path(__file__).parent.parent / "sessions"
SESSION_CONFIG = SESSION_DIR / ".current_session.json"
DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"


def get_current_session() -> dict:
    """Get current session info."""
    if SESSION_CONFIG.exists():
        with open(SESSION_CONFIG) as f:
            return json.load(f)
    return {"name": "default", "created": None, "path": str(DEFAULT_DATA_DIR)}


def set_current_session(name: str, path: str):
    """Set current session."""
    SESSION_DIR.mkdir(exist_ok=True)
    config = {
        "name": name,
        "created": datetime.now().isoformat(),
        "path": path,
    }
    with open(SESSION_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)
    return config


def new_session(name: str) -> dict:
    """Create a new experiment session."""
    # Sanitize name
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"{safe_name}_{timestamp}"
    
    # Create session directory
    session_path = SESSION_DIR / session_name
    session_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (session_path / "data").mkdir(exist_ok=True)
    (session_path / "figures").mkdir(exist_ok=True)
    
    # Set as current session
    config = set_current_session(session_name, str(session_path))
    
    # Create session info file
    info = {
        "name": name,
        "session_id": session_name,
        "created": config["created"],
        "description": "",
    }
    with open(session_path / "session_info.json", 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"✓ Created new session: {session_name}")
    print(f"  Database: {session_path}/data/experiments.db")
    print(f"  Figures:  {session_path}/figures/")
    print(f"\nRun experiments with: python -m src.experiment --full-experiment")
    
    return config


def list_sessions():
    """List all sessions."""
    if not SESSION_DIR.exists():
        print("No sessions found.")
        return []
    
    current = get_current_session()
    sessions = []
    
    print("\n📁 Experiment Sessions\n" + "=" * 50)
    
    for item in sorted(SESSION_DIR.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            info_file = item / "session_info.json"
            if info_file.exists():
                with open(info_file) as f:
                    info = json.load(f)
                is_current = item.name == current.get("name", "")
                marker = "→ " if is_current else "  "
                print(f"{marker}{item.name}")
                print(f"    Created: {info.get('created', 'unknown')}")
                
                # Count runs if db exists
                db_path = item / "data" / "experiments.db"
                if db_path.exists():
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    try:
                        cursor = conn.execute("SELECT COUNT(*) FROM runs")
                        count = cursor.fetchone()[0]
                        print(f"    Runs: {count}")
                    except sqlite3.OperationalError:
                        # Table might not exist yet
                        print("    Runs: 0 (no data)")
                    finally:
                        conn.close()
                
                sessions.append(item.name)
    
    if not sessions:
        print("  (no sessions yet)")
    
    print(f"\nCurrent: {current.get('name', 'default')}")
    return sessions


def use_session(name: str):
    """Switch to an existing session."""
    session_path = SESSION_DIR / name
    
    if not session_path.exists():
        print(f"❌ Session not found: {name}")
        print("   Use 'python -m src.session list' to see available sessions")
        return None
    
    config = set_current_session(name, str(session_path))
    print(f"✓ Switched to session: {name}")
    return config


def archive_current():
    """Archive current session and switch to a new one."""
    current = get_current_session()
    
    if current["name"] == "default":
        # Archive the default data folder
        if DEFAULT_DATA_DIR.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"archived_{timestamp}"
            archive_path = SESSION_DIR / archive_name
            archive_path.mkdir(parents=True, exist_ok=True)
            
            # Move data files
            shutil.move(str(DEFAULT_DATA_DIR), str(archive_path / "data"))
            DEFAULT_DATA_DIR.mkdir(exist_ok=True)
            
            # Move figures
            figures_dir = Path(__file__).parent.parent / "figures"
            if figures_dir.exists():
                shutil.move(str(figures_dir), str(archive_path / "figures"))
                figures_dir.mkdir(exist_ok=True)
            
            print(f"✓ Archived default session to: {archive_name}")
    else:
        print(f"✓ Current session archived: {current['name']}")
    
    # Reset to default
    set_current_session("default", str(DEFAULT_DATA_DIR))
    print("✓ Switched to fresh default session")


def get_session_db_path() -> Path:
    """Get database path for current session."""
    session = get_current_session()
    if session["name"] == "default":
        return DEFAULT_DATA_DIR / "experiments.db"
    return Path(session["path"]) / "data" / "experiments.db"


def get_session_figures_path() -> Path:
    """Get figures path for current session."""
    session = get_current_session()
    if session["name"] == "default":
        return Path(__file__).parent.parent / "figures"
    return Path(session["path"]) / "figures"


def compare_sessions(session1: str, session2: str) -> dict:
    """
    Compare metrics between two sessions.

    Args:
        session1: First session name
        session2: Second session name

    Returns:
        Dictionary with comparison metrics
    """
    import sqlite3
    import pandas as pd

    results = {"session1": session1, "session2": session2, "metrics": {}}

    for session_name, key in [(session1, "s1"), (session2, "s2")]:
        # Handle "default" session
        if session_name == "default":
            db_path = DEFAULT_DATA_DIR / "experiments.db"
        else:
            db_path = SESSION_DIR / session_name / "data" / "experiments.db"

        if not db_path.exists():
            print(f"❌ Database not found for session: {session_name}")
            return results

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Get run statistics
            runs = pd.read_sql_query("SELECT * FROM runs", conn)
            quality = pd.read_sql_query("SELECT * FROM quality_scores", conn)

            results["metrics"][key] = {
                "name": session_name,
                "total_runs": len(runs),
                "total_cost": runs["total_cost"].sum() if "total_cost" in runs else 0,
                "avg_cost": runs["total_cost"].mean() if "total_cost" in runs else 0,
                "models": runs["model"].unique().tolist() if "model" in runs else [],
                "workflows": runs["workflow"].unique().tolist() if "workflow" in runs else [],
            }

            if not quality.empty and "combined_score" in quality.columns:
                results["metrics"][key]["avg_quality"] = quality["combined_score"].mean()
            else:
                results["metrics"][key]["avg_quality"] = None

        except Exception as e:
            print(f"❌ Error reading session {session_name}: {e}")
            results["metrics"][key] = {"name": session_name, "error": str(e)}
        finally:
            conn.close()

    # Calculate differences
    if "s1" in results["metrics"] and "s2" in results["metrics"]:
        s1 = results["metrics"]["s1"]
        s2 = results["metrics"]["s2"]

        if "error" not in s1 and "error" not in s2:
            results["comparison"] = {
                "run_diff": s2["total_runs"] - s1["total_runs"],
                "cost_diff": s2["total_cost"] - s1["total_cost"],
                "cost_ratio": s2["total_cost"] / s1["total_cost"] if s1["total_cost"] > 0 else None,
            }
            if s1["avg_quality"] and s2["avg_quality"]:
                results["comparison"]["quality_diff"] = s2["avg_quality"] - s1["avg_quality"]

    return results


def print_session_comparison(session1: str, session2: str):
    """Print a formatted comparison between two sessions."""
    results = compare_sessions(session1, session2)

    print(f"\n📊 Session Comparison: {session1} vs {session2}")
    print("=" * 60)

    for key, label in [("s1", session1), ("s2", session2)]:
        if key in results["metrics"]:
            m = results["metrics"][key]
            if "error" in m:
                print(f"\n{label}: Error - {m['error']}")
            else:
                print(f"\n{label}:")
                print(f"  Runs:     {m['total_runs']}")
                print(f"  Cost:     ${m['total_cost']:.4f}")
                print(f"  Avg Cost: ${m['avg_cost']:.6f}/run")
                if m["avg_quality"]:
                    print(f"  Quality:  {m['avg_quality']:.1f}")
                print(f"  Workflows: {', '.join(m['workflows'][:5])}")

    if "comparison" in results:
        c = results["comparison"]
        print(f"\n📈 Difference ({session2} - {session1}):")
        print(f"  Runs:  {c['run_diff']:+d}")
        print(f"  Cost:  ${c['cost_diff']:+.4f}")
        if c["cost_ratio"]:
            print(f"  Ratio: {c['cost_ratio']:.2f}x")
        if "quality_diff" in c:
            print(f"  Quality: {c['quality_diff']:+.1f}")

    print("=" * 60)
    return results


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "new":
        name = sys.argv[2] if len(sys.argv) > 2 else f"session_{datetime.now().strftime('%Y%m%d')}"
        new_session(name)
    
    elif command == "list":
        list_sessions()
    
    elif command == "use":
        if len(sys.argv) < 3:
            print("Usage: python -m src.session use <session_name>")
            return
        use_session(sys.argv[2])
    
    elif command == "archive":
        archive_current()
    
    elif command == "current":
        session = get_current_session()
        print(f"Current session: {session['name']}")
        print(f"Database: {get_session_db_path()}")
        print(f"Figures: {get_session_figures_path()}")

    elif command == "compare":
        if len(sys.argv) < 4:
            print("Usage: python -m src.session compare <session1> <session2>")
            print("       Use 'default' for the default session")
            return
        print_session_comparison(sys.argv[2], sys.argv[3])

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
