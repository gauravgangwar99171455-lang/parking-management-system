"""
ParkSmart Pro — Backup & Recovery Automated Tests
"""

import unittest
import tempfile
from pathlib import Path
from database.connection import init_database
from services.backup_service import BackupService
from database.migrations import check_integrity
import config

class TestBackupService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_backup.db"
        self.backup_dir = Path(self.temp_dir.name) / "backups"
        config.DB_PATH = self.db_path
        config.BACKUP_DIR = self.backup_dir
        init_database(custom_path=self.db_path, seed_defaults=True)
        self.backup_service = BackupService()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_backup_creation_and_integrity(self):
        """Verify creating a live SQLite backup produces a valid, readable database file."""
        ok, backup_file, msg = self.backup_service.create_backup()
        self.assertTrue(ok, msg)
        self.assertIsNotNone(backup_file)
        self.assertTrue(backup_file.exists())

        # Verify integrity of backup
        is_ok, msgs = check_integrity(backup_file)
        self.assertTrue(is_ok)
        self.assertIn("ok", msgs)

    def test_backup_restore_and_safety_snapshot(self):
        """Verify restoring backup creates a safety snapshot and preserves healthy integrity."""
        # 1. Take initial backup
        ok_b, backup_file, _ = self.backup_service.create_backup()
        self.assertTrue(ok_b)

        # 2. Restore from backup
        ok_r, r_msg = self.backup_service.restore_backup(backup_file)
        self.assertTrue(ok_r, r_msg)

        # 3. Verify safety snapshot was created
        safety_backups = list(self.backup_dir.glob("pre_restore_safety_backup_*.db"))
        self.assertGreaterEqual(len(safety_backups), 1)

if __name__ == "__main__":
    unittest.main()
