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
                    except:
                        pass
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
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
