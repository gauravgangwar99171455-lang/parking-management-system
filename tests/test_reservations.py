"""
ParkSmart Pro — Reservation Service Automated Tests
"""

import unittest
import tempfile
from pathlib import Path
from database.connection import init_database
from services.reservation_service import ReservationService
from services.parking_service import ParkingService
import config

class TestReservationService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_res.db"
        config.DB_PATH = self.db_path
        init_database(custom_path=self.db_path, seed_defaults=True)
        self.res_service = ReservationService()
        self.parking = ParkingService()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_cancel_reservation(self):
        """Verify successful advance reservation creation and subsequent cancellation."""
        slots = self.parking.get_slots(category="CAR", status="AVAILABLE")
        self.assertTrue(len(slots) > 0)
        target_slot = slots[0]

        ok, res, msg = self.res_service.create_reservation(
            customer_name="Priya Sharma",
            customer_phone="9876543210",
            vehicle_reg="KA-05-RS-1234",
            category="CAR",
            slot_id=target_slot.id,
            start_time_str="2026-10-25 10:00:00",
            end_time_str="2026-10-25 14:00:00",
        )
        self.assertTrue(ok, msg)
        self.assertIsNotNone(res)
        self.assertEqual(res.status, "CONFIRMED")

        # Cancel reservation
        ok_cancel, cancel_msg = self.res_service.cancel_reservation(res.id, reason="Customer requested")
        self.assertTrue(ok_cancel, cancel_msg)

        all_res = self.res_service.get_reservations()
        matched = [r for r in all_res if r.id == res.id]
        self.assertEqual(matched[0].status, "CANCELLED")

    def test_overlapping_reservation_rejection(self):
        """Verify the system strictly blocks overlapping bookings on the same slot."""
        slots = self.parking.get_slots(category="CAR", status="AVAILABLE")
        target_slot = slots[0]

        # 1. First booking: 10:00 to 14:00
        ok1, res1, _ = self.res_service.create_reservation(
            customer_name="Rohan Gupta",
            customer_phone="9876500001",
            vehicle_reg="DL-03-RG-1111",
            category="CAR",
            slot_id=target_slot.id,
            start_time_str="2026-10-25 10:00:00",
            end_time_str="2026-10-25 14:00:00",
        )
        self.assertTrue(ok1)

        # 2. Overlapping booking: 12:00 to 16:00 (overlaps 12:00 - 14:00)
        ok2, res2, msg2 = self.res_service.create_reservation(
            customer_name="Aditya Verma",
            customer_phone="9876500002",
            vehicle_reg="HR-26-AV-2222",
            category="CAR",
            slot_id=target_slot.id,
            start_time_str="2026-10-25 12:00:00",
            end_time_str="2026-10-25 16:00:00",
        )
        self.assertFalse(ok2)
        self.assertIsNone(res2)
        self.assertIn("already reserved", msg2)

if __name__ == "__main__":
    unittest.main()
