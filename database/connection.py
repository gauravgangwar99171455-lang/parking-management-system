"""
ParkSmart Pro — Database Connection & Transaction Manager
TQM Quality Attribute: Reliability & Fault Tolerance (ISO/IEC 25010)
"""

import sqlite3
import hashlib
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator
import config
from utils.logger import get_logger

logger = get_logger("database")

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """Generate secure salted PBKDF2-HMAC-SHA256 password hash."""
    if salt is None:
        salt = os.urandom(config.PASSWORD_SALT_BYTES)
    salt_hex = salt.hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        config.PBKDF2_ITERATIONS
    ).hex()
    return pwd_hash, salt_hex

def verify_password(password: str, salt_hex: str, expected_hash: str) -> bool:
    """Verify password against stored salt and PBKDF2 hash using constant-time comparison."""
    try:
        salt = bytes.fromhex(salt_hex)
        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            config.PBKDF2_ITERATIONS
        ).hex()
        import hmac
        return hmac.compare_digest(computed_hash, expected_hash)
    except Exception as e:
        logger.error(f"Error during password verification: {e}")
        return False

def get_db_connection(custom_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Establish a high-performance SQLite connection with foreign keys and WAL mode.
    """
    db_file = custom_path or config.DB_PATH
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(
        str(db_file),
        timeout=10.0,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row

    # Performance & Concurrency Pragmas
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    
    return conn

@contextmanager
def get_db_cursor(conn: Optional[sqlite3.Connection] = None, commit: bool = True) -> Generator[sqlite3.Cursor, None, None]:
    """
    Context manager for database cursor with automatic commit/rollback semantics.
    """
    owns_conn = conn is None
    if owns_conn:
        conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database transaction error (rolled back): {e}")
        raise
    finally:
        if owns_conn and conn:
            conn.close()

def init_database(custom_path: Optional[Path] = None, seed_defaults: bool = True) -> None:
    """
    Execute schema.sql and seed baseline roles, tariffs, and admin account.
    """
    conn = get_db_connection(custom_path)
    try:
        with conn:
            with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            
            if seed_defaults:
                _seed_initial_data(conn)
        logger.info(f"Database initialized successfully at {custom_path or config.DB_PATH}")
    finally:
        conn.close()

def _seed_initial_data(conn: sqlite3.Connection) -> None:
    """Seed baseline roles, default tariffs, zones, slots, and system accounts."""
    cur = conn.cursor()

    # 1. Seed Roles
    cur.execute("SELECT COUNT(*) FROM roles")
    if cur.fetchone()[0] == 0:
        roles = [
            ("admin", "Full system administrator with tariff, user, and backup privileges"),
            ("operator", "Parking gate operator with entry, exit, billing, and reservation privileges"),
            ("auditor", "Read-only auditor with dashboard, search, and reporting privileges"),
        ]
        cur.executemany("INSERT INTO roles (name, description) VALUES (?, ?)", roles)

    # 2. Seed Default Admin, Operator, and Auditor Users
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id, name FROM roles")
        role_map = {row["name"]: row["id"] for row in cur.fetchall()}

        admin_hash, admin_salt = hash_password("admin123")
        op_hash, op_salt = hash_password("operator123")
        audit_hash, audit_salt = hash_password("auditor123")

        users_data = [
            ("admin", admin_hash, admin_salt, "System Administrator", role_map["admin"]),
            ("operator", op_hash, op_salt, "Front Desk Operator", role_map["operator"]),
            ("auditor", audit_hash, audit_salt, "Quality & Audit Inspector", role_map["auditor"]),
        ]
        cur.executemany("""
            INSERT INTO users (username, password_hash, salt, full_name, role_id)
            VALUES (?, ?, ?, ?, ?)
        """, users_data)

    # 3. Seed Default Tariffs
    cur.execute("SELECT COUNT(*) FROM parking_tariffs")
    if cur.fetchone()[0] == 0:
        tariffs = [
            # code, base_duration_mins, base_rate_cents, hourly_rate_cents, daily_max_cents, grace_mins, lost_fee_cents
            ("TWO_WHEELER", 60, 1500, 1000, 5000, 15, 3000),   # Base $15 (1h), $10/hr after, $50 max
            ("CAR",         60, 3000, 2000, 10000, 15, 6000),  # Base $30 (1h), $20/hr after, $100 max
            ("SUV",         60, 4000, 2500, 12000, 15, 7500),  # Base $40 (1h), $25/hr after, $120 max
            ("COMMERCIAL",  60, 6000, 4000, 18000, 15, 10000), # Base $60 (1h), $40/hr after, $180 max
            ("EV",          60, 2500, 1500, 8000, 20, 5000),   # Base $25 (1h), $15/hr after, $80 max
        ]
        cur.executemany("""
            INSERT INTO parking_tariffs 
            (vehicle_category, base_duration_minutes, base_rate_cents, hourly_rate_cents, daily_max_cents, grace_period_minutes, lost_ticket_fee_cents)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tariffs)

    # 4. Seed Default Zones
    cur.execute("SELECT COUNT(*) FROM parking_zones")
    if cur.fetchone()[0] == 0:
        zones = [
            ("ZONE-A", "Zone A — Ground Floor (Standard & Priority)", 0, "Near entrance and exit gate"),
            ("ZONE-B", "Zone B — First Floor (Sedans & Compact Cars)", 1, "Covered multi-level bay"),
            ("ZONE-C", "Zone C — Second Floor (SUVs & Large Vehicles)", 2, "Wide parking stalls"),
            ("ZONE-D", "Zone D — Basement (Two-Wheelers & EV Charging)", -1, "Equipped with charging stations"),
            ("ZONE-E", "Zone E — Commercial Bay (Buses & Delivery Vans)", 0, "High ceiling commercial dock"),
        ]
        cur.executemany("""
            INSERT INTO parking_zones (code, name, floor_number, description)
            VALUES (?, ?, ?, ?)
        """, zones)

    # 5. Seed Initial Slots
    cur.execute("SELECT COUNT(*) FROM parking_slots")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id, code FROM parking_zones")
        zone_map = {row["code"]: row["id"] for row in cur.fetchall()}

        slots = []
        # Zone A: 12 Car slots
        for i in range(1, 13):
            slots.append((f"A-{i:02d}", zone_map["ZONE-A"], "CAR", "AVAILABLE"))
        # Zone B: 12 Car slots
        for i in range(1, 13):
            slots.append((f"B-{i:02d}", zone_map["ZONE-B"], "CAR", "AVAILABLE"))
        # Zone C: 10 SUV slots
        for i in range(1, 11):
            slots.append((f"C-{i:02d}", zone_map["ZONE-C"], "SUV", "AVAILABLE"))
        # Zone D: 12 Two-Wheeler & 6 EV slots
        for i in range(1, 13):
            slots.append((f"D-TW-{i:02d}", zone_map["ZONE-D"], "TWO_WHEELER", "AVAILABLE"))
        for i in range(1, 7):
            slots.append((f"D-EV-{i:02d}", zone_map["ZONE-D"], "EV", "AVAILABLE"))
        # Zone E: 6 Commercial slots
        for i in range(1, 7):
            slots.append((f"E-{i:02d}", zone_map["ZONE-E"], "COMMERCIAL", "AVAILABLE"))

        cur.executemany("""
            INSERT INTO parking_slots (slot_code, zone_id, supported_category, status)
            VALUES (?, ?, ?, ?)
        """, slots)
