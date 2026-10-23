"""
ParkSmart Pro — Parking Management & Entry Workflow Automated Tests
"""

import unittest
import tempfile
from pathlib import Path
from database.connection import init_database
from services.parking_service import ParkingService
import config

class TestParkingService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_parking.db"
        config.DB_PATH = self.db_path
        init_database(custom_path=self.db_path, seed_defaults=True)
        self.parking = ParkingService()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_successful_vehicle_entry(self):
        """Verify normal vehicle entry generates ticket and changes slot to OCCUPIED."""
        ok, session, msg = self.parking.register_vehicle_entry(
            vehicle_reg="KA-01-MJ-9999",
            category="CAR"
        )
        self.assertTrue(ok, msg)
        self.assertIsNotNone(session)
        self.assertTrue(session.ticket_number.startswith("TKT-"))
        self.assertEqual(session.vehicle_registration, "KA01MJ9999")
        self.assertEqual(session.status, "ACTIVE")

        # Verify slot status changed to OCCUPIED
        slots = self.parking.get_slots(search_code=session.slot_code)
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].status, "OCCUPIED")

    def test_prevent_duplicate_active_entry(self):
        """Verify the system strictly blocks a vehicle from entering twice while active."""
        ok1, sess1, _ = self.parking.register_vehicle_entry("MH-12-AB-1234", "CAR")
        self.assertTrue(ok1)

        ok2, sess2, msg2 = self.parking.register_vehicle_entry("MH-12-AB-1234", "CAR")
        self.assertFalse(ok2)
        self.assertIsNone(sess2)
        self.assertIn("already parked inside", msg2)

    def test_invalid_vehicle_registration(self):
        """Verify empty or malformed vehicle registration is rejected."""
        ok, _, msg = self.parking.register_vehicle_entry("", "CAR")
        self.assertFalse(ok)
        self.assertIn("empty", msg.lower())

        ok2, _, msg2 = self.parking.register_vehicle_entry("A", "CAR")
        self.assertFalse(ok2)
        self.assertIn("too short", msg2.lower())

    def test_slot_status_update(self):
        """Verify updating slot status to MAINTENANCE and back to AVAILABLE."""
        slots = self.parking.get_slots(category="CAR", status="AVAILABLE")
        self.assertTrue(len(slots) > 0)
        target_slot = slots[0]

        ok, msg = self.parking.update_slot_status(target_slot.id, "MAINTENANCE")
        self.assertTrue(ok, msg)

        updated = self.parking.get_slots(search_code=target_slot.slot_code)[0]
        self.assertEqual(updated.status, "MAINTENANCE")

        ok2, _ = self.parking.update_slot_status(target_slot.id, "AVAILABLE")
        self.assertTrue(ok2)

if __name__ == "__main__":
    unittest.main()
