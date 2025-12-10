"""
Database connection management with thread safety.

Now session-aware: uses get_session_db_path() by default to route
experiment data to the current session's database.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional

# Global lock for thread-safe database writes
_db_lock = threading.Lock()


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Get a database connection with WAL mode for concurrent access.

    Args:
        db_path: Optional custom database path. If None, uses current session's DB.

    Returns:
        SQLite connection with row factory enabled
    """
    if db_path is None:
        # Import here to avoid circular import
        from ..session import get_session_db_path
        path = get_session_db_path()
    else:
        path = db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    return conn


def get_lock() -> threading.Lock:
    """Get the global database lock for write operations."""
    return _db_lock


def with_lock(func):
    """Decorator to wrap a function with the database lock."""
    def wrapper(*args, **kwargs):
        with _db_lock:
            return func(*args, **kwargs)
    return wrapper
