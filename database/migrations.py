"""
ParkSmart Pro — Database Migrations and Maintenance
TQM Principle: Continuous Verification & Prevention
"""

import sqlite3
from pathlib import Path
from typing import Tuple, List
from database.connection import get_db_connection
from utils.logger import get_logger

logger = get_logger("migrations")

def check_integrity(db_path: Path = None) -> Tuple[bool, List[str]]:
    """
    Run low-level SQLite PRAGMA integrity_check and foreign_key_check.
    Returns (is_healthy, messages).
    """
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        results = [row[0] for row in cur.fetchall()]
        
        cur.execute("PRAGMA foreign_key_check;")
        fk_errors = cur.fetchall()
        
        is_ok = len(results) == 1 and results[0] == "ok" and len(fk_errors) == 0
        messages = results[:]
        if fk_errors:
            messages.append(f"Foreign key violations found: {len(fk_errors)}")
            for err in fk_errors:
                messages.append(f"Table {err[0]}, rowid {err[1]}, references {err[2]}")
        
        return is_ok, messages
    except Exception as e:
        logger.error(f"Integrity check failed: {e}")
        return False, [str(e)]
    finally:
        conn.close()

def get_database_stats(db_path: Path = None) -> dict:
    """Return database file size, page count, and row counts across all tables."""
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        tables = [
            "roles", "users", "parking_zones", "parking_slots",
            "parking_tariffs", "parking_sessions", "reservations",
            "payments", "audit_logs", "import_logs"
        ]
        counts = {}
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                counts[t] = cur.fetchone()[0]
            except sqlite3.OperationalError:
                counts[t] = 0
        
        cur.execute("PRAGMA page_count;")
        page_count = cur.fetchone()[0]
        cur.execute("PRAGMA page_size;")
        page_size = cur.fetchone()[0]
        
        return {
            "table_counts": counts,
            "page_count": page_count,
            "page_size_bytes": page_size,
            "total_size_bytes": page_count * page_size
        }
    finally:
        conn.close()
