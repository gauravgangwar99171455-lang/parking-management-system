"""
ParkSmart Pro — Demo Dataset Generator
Populates realistic operational data for testing and college project demonstration.
"""

import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

# Ensure parent directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.connection import get_db_connection, init_database
from config import DEFAULT_VEHICLE_CATEGORIES

SAMPLE_REG_PREFIXES = ["KA-01", "KA-05", "MH-02", "MH-12", "DL-03", "DL-08", "TS-09", "TN-07", "HR-26", "UP-16"]
SAMPLE_NAMES = [
    "Aarav Sharma", "Aditi Patel", "Rohan Verma", "Sneha Iyer", "Vikram Singh",
    "Pooja Nair", "Rahul Mehta", "Ananya Das", "Karthik Reddy", "Priya Kulkarni",
    "Arjun Sen", "Neha Gupta", "Siddharth Rao", "Divya Menon", "Amitabh Joshi"
]

def seed_demo(num_historical: int = 150, num_active: int = 18):
    print("Initializing clean database...")
    init_database(seed_defaults=True)

    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Fetch available slots
        cur.execute("SELECT id, slot_code, supported_category FROM parking_slots ORDER BY id ASC")
        slots = [dict(r) for r in cur.fetchall()]
        if not slots:
            print("Error: No parking slots found.")
            return

        print(f"Generating {num_historical} completed historical sessions...")
        now = datetime.now()
        historical_records = []
        payment_records = []

        categories = [c["code"] for c in DEFAULT_VEHICLE_CATEGORIES]

        for i in range(1, num_historical + 1):
            slot = random.choice(slots)
            category = slot["supported_category"]
            prefix = random.choice(SAMPLE_REG_PREFIXES)
            reg = f"{prefix}-{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}-{random.randint(1000, 9999)}"
            ticket = f"TKT-HIST-{i:05d}"

            # Random entry between 1 and 30 days ago
            days_ago = random.randint(1, 30)
            entry_hour = random.randint(7, 21)
            entry_minute = random.randint(0, 59)
            entry_dt = now - timedelta(days=days_ago, hours=now.hour - entry_hour, minutes=now.minute - entry_minute)

            # Random duration: 25 mins to 9 hours
            duration_mins = random.randint(25, 540)
            exit_dt = entry_dt + timedelta(minutes=duration_mins)

            # Approximate rate
            hourly_rate = 2000 if category == "CAR" else (1000 if category == "TWO_WHEELER" else 2500)
            hours = max(1, duration_mins // 60)
            gross = 3000 + (hours * hourly_rate)
            discount = 0 if random.random() > 0.25 else int(gross * 0.20)
            net = gross - discount

            historical_records.append((
                ticket, reg, category, slot["id"],
                entry_dt.strftime("%Y-%m-%d %H:%M:%S"),
                exit_dt.strftime("%Y-%m-%d %H:%M:%S"),
                'COMPLETED', duration_mins, gross, discount, net,
                '{"seeded": true}', "Demo Historical Data", 1
            ))

        cur.executemany("""
            INSERT INTO parking_sessions (
                ticket_number, vehicle_registration, vehicle_category, slot_id,
                entry_time, exit_time, status, duration_minutes, gross_amount_cents,
                discount_cents, net_amount_cents, tariff_snapshot, notes, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, historical_records)

        # Retrieve session IDs to create payments
        cur.execute("SELECT id, net_amount_cents, exit_time FROM parking_sessions WHERE notes = 'Demo Historical Data'")
        for r in cur.fetchall():
            method = random.choice(["CASH", "CARD", "UPI", "WALLET"])
            payment_records.append((
                r["id"], r["net_amount_cents"], method, 'PAID',
                f"TXN-HIST-{r['id']}", 1, r["exit_time"]
            ))

        cur.executemany("""
            INSERT INTO payments (
                session_id, amount_cents, payment_method, payment_status,
                transaction_reference, cashier_user_id, payment_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, payment_records)

        print(f"Generating {num_active} currently active parking sessions...")
        # Pick distinct slots for active sessions
        active_slots = random.sample(slots, min(num_active, len(slots)))
        active_records = []
        for idx, s in enumerate(active_slots, 1):
            category = s["supported_category"]
            prefix = random.choice(SAMPLE_REG_PREFIXES)
            reg = f"{prefix}-{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}-{random.randint(1000, 9999)}"
            ticket = f"TKT-{now.strftime('%Y%m%d')}-{idx:04d}"

            # Entry 10 minutes to 5 hours ago today
            mins_ago = random.randint(10, 300)
            entry_dt = now - timedelta(minutes=mins_ago)

            active_records.append((
                ticket, reg, category, s["id"],
                entry_dt.strftime("%Y-%m-%d %H:%M:%S"),
                'ACTIVE', 1
            ))

            # Mark slot as OCCUPIED
            cur.execute("UPDATE parking_slots SET status = 'OCCUPIED' WHERE id = ?", (s["id"],))

        cur.executemany("""
            INSERT INTO parking_sessions (
                ticket_number, vehicle_registration, vehicle_category, slot_id,
                entry_time, status, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, active_records)

        print("Generating upcoming reservations...")
        # Create 5 reservations for available slots
        cur.execute("SELECT id, supported_category FROM parking_slots WHERE status = 'AVAILABLE' LIMIT 5")
        avail_slots = cur.fetchall()
        for idx, s in enumerate(avail_slots, 1):
            name = random.choice(SAMPLE_NAMES)
            phone = f"98765{random.randint(10000, 99999)}"
            prefix = random.choice(SAMPLE_REG_PREFIXES)
            reg = f"{prefix}-RS-{random.randint(1000, 9999)}"
            code = f"RES-{now.strftime('%Y%m%d')}-{idx:03d}"
            start_dt = now + timedelta(hours=random.randint(1, 12))
            end_dt = start_dt + timedelta(hours=random.randint(2, 6))

            cur.execute("""
                INSERT INTO reservations (
                    reservation_code, customer_name, customer_phone, vehicle_registration,
                    vehicle_category, slot_id, start_time, end_time, status, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', 1)
            """, (code, name, phone, reg, s["supported_category"], s["id"],
                  start_dt.strftime("%Y-%m-%d %H:%M:%S"), end_dt.strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        print(f"Demo data successfully seeded! Generated {num_historical} historical sessions, {num_active} active sessions, 5 reservations.")

    finally:
        conn.close()

if __name__ == "__main__":
    seed_demo()
