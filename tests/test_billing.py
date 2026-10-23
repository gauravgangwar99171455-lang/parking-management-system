"""
ParkSmart Pro — Billing & Vehicle Exit Automated Tests
TQM Invariant: Financial Precision & Safe Transaction Rollback
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from database.connection import init_database, get_db_connection
from services.parking_service import ParkingService
from services.billing_service import BillingService
import config

class TestBillingService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_billing.db"
        config.DB_PATH = self.db_path
        init_database(custom_path=self.db_path, seed_defaults=True)
        self.parking = ParkingService()
        self.billing = BillingService()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_grace_period_zero_charge(self):
        """Parking duration within grace period (15 mins) must be charged $0.00."""
        t_entry = "2026-10-24 10:00:00"
        t_exit = "2026-10-24 10:12:00" # 12 mins <= 15 mins grace
        bill = self.billing.calculate_bill(t_entry, t_exit, "CAR")
        self.assertEqual(bill["duration_minutes"], 12)
        self.assertEqual(bill["gross_cents"], 0)
        self.assertEqual(bill["net_cents"], 0)
        self.assertIn("Grace Period", bill["reason"])

    def test_base_duration_charge(self):
        """Parking duration <= 60 mins must be charged the base rate ($30.00 for CAR)."""
        t_entry = "2026-10-24 10:00:00"
        t_exit = "2026-10-24 10:45:00" # 45 mins
        bill = self.billing.calculate_bill(t_entry, t_exit, "CAR")
        self.assertEqual(bill["duration_minutes"], 45)
        self.assertEqual(bill["gross_cents"], 3000) # $30.00
        self.assertEqual(bill["net_cents"], 3000)

    def test_additional_hourly_charge(self):
        """1h 45m (105 mins) = Base 1h ($30.00) + 1 extra hour ($20.00) = $50.00 (5000 cents)."""
        t_entry = "2026-10-24 10:00:00"
        t_exit = "2026-10-24 11:45:00" # 1h 45m
        bill = self.billing.calculate_bill(t_entry, t_exit, "CAR")
        self.assertEqual(bill["duration_minutes"], 105)
        self.assertEqual(bill["gross_cents"], 5000) # $50.00
        self.assertEqual(bill["net_cents"], 5000)

    def test_daily_maximum_cap(self):
        """8 hours on CAR at $30 + (7 * $20) = $170, but capped at daily max ($100 = 10000 cents)."""
        t_entry = "2026-10-24 08:00:00"
        t_exit = "2026-10-24 16:00:00" # 8 hours
        bill = self.billing.calculate_bill(t_entry, t_exit, "CAR")
        self.assertEqual(bill["gross_cents"], 10000) # Capped at daily max $100

    def test_authorized_discount_application(self):
        """Campus staff discount (50%) on a $50 bill should yield $25 net."""
        t_entry = "2026-10-24 10:00:00"
        t_exit = "2026-10-24 11:45:00" # $50 gross
        bill = self.billing.calculate_bill(t_entry, t_exit, "CAR", discount_code="STAFF")
        self.assertEqual(bill["gross_cents"], 5000)
        self.assertEqual(bill["discount_cents"], 2500)
        self.assertEqual(bill["net_cents"], 2500)

    def test_atomic_checkout_transaction(self):
        """Full entry -> exit cycle: verifies session completes, payment is logged, slot released."""
        ok_entry, session, _ = self.parking.register_vehicle_entry("DL-04-TX-1000", "CAR")
        self.assertTrue(ok_entry)
        slot_id = session.slot_id

        # Verify slot is occupied
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM parking_slots WHERE id = ?", (slot_id,))
        self.assertEqual(cur.fetchone()["status"], "OCCUPIED")
        conn.close()

        # Process exit
        ok_exit, receipt, msg = self.billing.process_exit_and_payment(
            session_id=session.id,
            payment_method="UPI"
        )
        self.assertTrue(ok_exit, msg)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["payment_method"], "UPI")

        # Verify session is COMPLETED
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT status, exit_time FROM parking_sessions WHERE id = ?", (session.id,))
        s_row = cur.fetchone()
        self.assertEqual(s_row["status"], "COMPLETED")
        self.assertIsNotNone(s_row["exit_time"])

        # Verify payment record exists
        cur.execute("SELECT * FROM payments WHERE session_id = ?", (session.id,))
        p_row = cur.fetchone()
        self.assertIsNotNone(p_row)
        self.assertEqual(p_row["payment_method"], "UPI")

        # Verify slot is released to AVAILABLE
        cur.execute("SELECT status FROM parking_slots WHERE id = ?", (slot_id,))
        self.assertEqual(cur.fetchone()["status"], "AVAILABLE")
        conn.close()

if __name__ == "__main__":
    unittest.main()
