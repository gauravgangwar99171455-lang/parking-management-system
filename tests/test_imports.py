"""
ParkSmart Pro — CSV Import Engine Automated Tests
TQM Principle: Rigorous Pre-Validation & Diagnostics
"""

import unittest
import tempfile
from pathlib import Path
from database.connection import init_database
from services.import_service import ImportService
from utils.export_helpers import export_rows_to_csv
import config

class TestImportService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_import.db"
        config.DB_PATH = self.db_path
        init_database(custom_path=self.db_path, seed_defaults=True)
        self.import_service = ImportService()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_slot_csv_validation_and_commit(self):
        """Verify validating and importing clean parking slots CSV."""
        csv_file = Path(self.temp_dir.name) / "test_slots.csv"
        headers = ["slot_code", "zone_code", "supported_category"]
        rows = [
            ["A-901", "ZONE-A", "CAR"],
            ["A-902", "ZONE-A", "CAR"],
            ["C-901", "ZONE-C", "SUV"],
        ]
        export_rows_to_csv(csv_file, headers, rows)

        res = self.import_service.validate_slot_csv(csv_file)
        self.assertTrue(res["success"])
        self.assertEqual(res["valid_count"], 3)
        self.assertEqual(res["invalid_count"], 0)

        ok_commit, msg = self.import_service.commit_slot_import(res["valid_rows"], "test_slots.csv")
        self.assertTrue(ok_commit, msg)

    def test_slot_csv_duplicate_and_invalid_detection(self):
        """Verify duplicate codes and invalid zones/categories are flagged as invalid rows."""
        csv_file = Path(self.temp_dir.name) / "bad_slots.csv"
        headers = ["slot_code", "zone_code", "supported_category"]
        rows = [
            ["A-01", "ZONE-A", "CAR"],       # Duplicate: A-01 already in seeded DB
            ["X-99", "INVALID_ZONE", "CAR"], # Invalid zone
            ["Y-88", "ZONE-B", "SPACESHIP"], # Invalid category
            ["Z-10", "ZONE-A", "CAR"],       # Valid
        ]
        export_rows_to_csv(csv_file, headers, rows)

        res = self.import_service.validate_slot_csv(csv_file)
        self.assertTrue(res["success"])
        self.assertEqual(res["valid_count"], 1)
        self.assertEqual(res["invalid_count"], 3)
        self.assertIn("already exists", res["invalid_rows"][0]["reasons"])
        self.assertIn("does not exist", res["invalid_rows"][1]["reasons"])
        self.assertIn("Invalid category", res["invalid_rows"][2]["reasons"])

    def test_missing_mandatory_columns(self):
        """Verify import engine rejects CSV missing mandatory column headers."""
        csv_file = Path(self.temp_dir.name) / "missing_cols.csv"
        headers = ["slot_code", "supported_category"] # zone_code is missing!
        rows = [["A-999", "CAR"]]
        export_rows_to_csv(csv_file, headers, rows)

        res = self.import_service.validate_slot_csv(csv_file)
        self.assertFalse(res["success"])
        self.assertIn("Missing mandatory columns", res["error"])

if __name__ == "__main__":
    unittest.main()
