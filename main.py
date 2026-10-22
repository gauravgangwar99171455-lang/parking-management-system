"""
ParkSmart Pro — Smart Parking Management System
Main Application Entry Point
Total Quality Management (TQM) Capstone Project

Author: B.Tech CSE Student
Standard: ISO 9001:2015 & ISO/IEC 25010 Compliant
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import init_database
from database.migrations import check_integrity
from utils.logger import get_logger

logger = get_logger("main")

def run_tests():
    """Run automated unittest test suite."""
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(PROJECT_ROOT / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

def run_benchmarks():
    """Run performance benchmarks on 10,000+ records."""
    import scripts.benchmark_search as bs
    import scripts.benchmark_reports as br
    print("\n--- Running Search Benchmark (PDCA Cycle 1) ---")
    bs.main()
    print("\n--- Running Reporting Benchmark (PDCA Cycle 3) ---")
    br.main()

def seed_data():
    """Seed rich demo operational data."""
    import scripts.seed_demo_data as sd
    sd.seed_demo()

def start_gui():
    """Launch modern Tkinter desktop interface."""
    logger.info("Initializing ParkSmart Pro Desktop Application...")
    # Verify database health on boot
    is_healthy, msgs = check_integrity()
    if not is_healthy:
        logger.error(f"Database integrity warning: {msgs}")

    from ui.app import ParkSmartApp
    app = ParkSmartApp()
    app.mainloop()

def main():
    parser = argparse.ArgumentParser(description="ParkSmart Pro — Smart Parking Management System")
    parser.add_argument("--gui", action="store_true", default=True, help="Launch desktop GUI (default)")
    parser.add_argument("--test", action="store_true", help="Run automated test suite")
    parser.add_argument("--benchmark", action="store_true", help="Run 10,000-record empirical benchmarks")
    parser.add_argument("--seed", action="store_true", help="Seed realistic demo data")

    args = parser.parse_args()

    # Priority command flags
    if args.test:
        run_tests()
    elif args.benchmark:
        run_benchmarks()
    elif args.seed:
        seed_data()
    else:
        start_gui()

if __name__ == "__main__":
    main()
