"""
ParkSmart Pro — Analytical Reports Automated Tests
"""

import unittest
import tempfile
from pathlib import Path
from database.connection import init_database
from services.parking_service import ParkingService
from services.billing_service import BillingService
from services.report_service import ReportService
import config

class TestReportService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_reports.db"
        config.DB_PATH = self.db_path
        init_database(custom_path=self.db_path, seed_defaults=True)
        self.parking = ParkingService()
        self.billing = BillingService()
        self.reports = ReportService()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dashboard_kpis_accuracy(self):
        """Verify dashboard KPIs correctly reflect active parking states."""
        kpi1 = self.reports.get_dashboard_kpis()
        init_available = kpi1["available_slots"]
        init_occupied = kpi1["occupied_slots"]

        # Register vehicle entry
        self.parking.register_vehicle_entry("KA-01-KP-1111", "CAR")

        kpi2 = self.reports.get_dashboard_kpis()
        self.assertEqual(kpi2["available_slots"], init_available - 1)
        self.assertEqual(kpi2["occupied_slots"], init_occupied + 1)
        self.assertEqual(kpi2["currently_parked"], 1)

    def test_financial_report_totals(self):
        """Verify completed session revenue is captured accurately in financial reports."""
        ok_entry, session, _ = self.parking.register_vehicle_entry("DL-08-FR-2222", "CAR")
        self.billing.process_exit_and_payment(session.id, payment_method="CASH")

        today_str = "2026-10-24"
        fin = self.reports.get_financial_report(today_str, today_str)
        self.assertEqual(fin["summary"]["total_completed_sessions"], 1)
        self.assertGreaterEqual(fin["summary"]["total_net_cents"], 0)

if __name__ == "__main__":
    unittest.main()
