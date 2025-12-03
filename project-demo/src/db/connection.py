"""
Database connection management with thread safety.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from ..config import DB_PATH

# Global lock for thread-safe database writes
_db_lock = threading.Lock()


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Get a database connection with WAL mode for concurrent access.
    
    Args:
        db_path: Optional custom database path
    
    Returns:
        SQLite connection with row factory enabled
    """
    path = db_path or DB_PATH
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
