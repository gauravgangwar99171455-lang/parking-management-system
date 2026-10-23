"""
ParkSmart Pro — Database & Constraint Automated Tests
TQM Quality Attribute: Reliability & Functional Correctness (ISO/IEC 25010)
"""

import unittest
import sqlite3
import tempfile
from pathlib import Path
from database.connection import init_database, get_db_connection
from database.migrations import check_integrity, get_database_stats

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_db.db"
        init_database(custom_path=self.db_path, seed_defaults=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_integrity(self):
        """Verify PRAGMA integrity_check passes on freshly initialized database."""
        is_ok, msgs = check_integrity(self.db_path)
        self.assertTrue(is_ok)
        self.assertIn("ok", msgs)

    def test_table_counts_and_structure(self):
        """Verify all core tables are created and default seeds exist."""
        stats = get_database_stats(self.db_path)
        counts = stats["table_counts"]
        self.assertEqual(counts["roles"], 3)
        self.assertEqual(counts["users"], 3)
        self.assertEqual(counts["parking_zones"], 5)
        self.assertGreater(counts["parking_slots"], 50)
        self.assertEqual(counts["parking_tariffs"], 5)

    def test_foreign_key_enforcement(self):
        """Verify SQLite blocks insert of slot with non-existent foreign key zone_id."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute("""
                INSERT INTO parking_slots (slot_code, zone_id, supported_category, status)
                VALUES ('INVALID-01', 9999, 'CAR', 'AVAILABLE')
            """)
        conn.close()

    def test_unique_slot_code_constraint(self):
        """Verify duplicate slot codes are rejected by SQLite unique constraint."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute("""
                INSERT INTO parking_slots (slot_code, zone_id, supported_category, status)
                VALUES ('A-01', 1, 'CAR', 'AVAILABLE')
            """)
        conn.close()

    def test_partial_index_active_session_uniqueness(self):
        """
        Verify SQLite partial index idx_unique_active_session prevents two ACTIVE
        sessions for the same vehicle registration.
        """
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO parking_sessions (
                ticket_number, vehicle_registration, vehicle_category, slot_id, entry_time, status
            ) VALUES ('TKT-TEST-001', 'KA01AB1234', 'CAR', 1, '2026-10-24 10:00:00', 'ACTIVE')
        """)
        conn.commit()

        # Second ACTIVE session for the same vehicle registration must fail!
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute("""
                INSERT INTO parking_sessions (
                    ticket_number, vehicle_registration, vehicle_category, slot_id, entry_time, status
                ) VALUES ('TKT-TEST-002', 'KA01AB1234', 'CAR', 2, '2026-10-24 10:15:00', 'ACTIVE')
            """)
        conn.close()

    def test_partial_index_active_slot_uniqueness(self):
        """
        Verify SQLite partial index idx_unique_active_slot_alloc prevents assigning
        the same slot to two concurrent ACTIVE sessions.
        """
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO parking_sessions (
                ticket_number, vehicle_registration, vehicle_category, slot_id, entry_time, status
            ) VALUES ('TKT-TEST-010', 'KA01AB1111', 'CAR', 3, '2026-10-24 10:00:00', 'ACTIVE')
        """)
        conn.commit()

        # Second ACTIVE session for the same slot must fail!
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute("""
                INSERT INTO parking_sessions (
                    ticket_number, vehicle_registration, vehicle_category, slot_id, entry_time, status
                ) VALUES ('TKT-TEST-011', 'KA01AB2222', 'CAR', 3, '2026-10-24 10:05:00', 'ACTIVE')
            """)
        conn.close()

if __name__ == "__main__":
    unittest.main()
