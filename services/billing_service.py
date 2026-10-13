"""
ParkSmart Pro — Billing & Vehicle Exit Service
TQM Quality Attribute: Financial Accuracy, Auditability & ACID Reliability
"""

import math
import json
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
from database.connection import get_db_connection
from models.parking_session import ParkingSession
from models.tariff import ParkingTariff
from models.payment import Payment
from services.audit_service import audit_service
from utils.logger import get_logger

logger = get_logger("billing_service")

# Preset Authorized Discounts
AUTHORIZED_DISCOUNTS = {
    "NONE": {"name": "No Discount", "pct": 0},
    "STAFF": {"name": "Campus Staff / Faculty (50%)", "pct": 50},
    "SENIOR": {"name": "Senior Citizen / Accessibility (25%)", "pct": 25},
    "FREQUENT": {"name": "Frequent Parker Loyalty (15%)", "pct": 15},
    "STUDENT": {"name": "Student Parking Pass (20%)", "pct": 20},
    "WAIVED": {"name": "Administrative Courtesy (100%)", "pct": 100},
}

class BillingService:
    def get_tariff_for_category(self, category: str) -> Optional[ParkingTariff]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM parking_tariffs WHERE vehicle_category = ? AND is_active = 1", (category,))
            row = cur.fetchone()
            if row:
                return ParkingTariff.from_row(row)
            return None
        finally:
            conn.close()

    def get_all_tariffs(self) -> List[ParkingTariff]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM parking_tariffs ORDER BY id ASC")
            return [ParkingTariff.from_row(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def update_tariff(self, tariff_id: int, base_duration_mins: int, base_rate_cents: int,
                      hourly_rate_cents: int, daily_max_cents: int, grace_mins: int,
                      lost_fee_cents: int) -> Tuple[bool, str]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE parking_tariffs
                SET base_duration_minutes = ?, base_rate_cents = ?,
                    hourly_rate_cents = ?, daily_max_cents = ?,
                    grace_period_minutes = ?, lost_ticket_fee_cents = ?,
                    updated_at = DATETIME('now', 'localtime')
                WHERE id = ?
            """, (base_duration_mins, base_rate_cents, hourly_rate_cents, daily_max_cents, grace_mins, lost_fee_cents, tariff_id))
            conn.commit()
            audit_service.log(
                action="UPDATE_TARIFF", entity_type="TARIFF", entity_id=str(tariff_id),
                details=f"Updated tariff {tariff_id}: base={base_rate_cents}, hourly={hourly_rate_cents}, max={daily_max_cents}"
            )
            return True, "Tariff rates updated successfully."
        except Exception as e:
            conn.rollback()
            return False, f"Failed to update tariff: {str(e)}"
        finally:
            conn.close()

    def calculate_bill(self, entry_time_str: str, exit_time_str: str, category: str,
                       discount_code: str = "NONE", custom_discount_cents: int = 0) -> Dict[str, Any]:
        """
        Compute precise parking bill according to configured tariff rules.
        TQM Deterministic Calculation:
        - Grace period: <= grace_period_minutes -> $0.00
        - Base duration: <= base_duration_minutes -> base_rate_cents
        - Extra hours: ceil((duration - base_duration) / 60) * hourly_rate_cents
        - Daily Cap: applied per 24-hour cycle
        """
        # Parse datetimes
        dt_entry = datetime.strptime(entry_time_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
        dt_exit = datetime.strptime(exit_time_str.split(".")[0], "%Y-%m-%d %H:%M:%S")

        duration_seconds = max(0, int((dt_exit - dt_entry).total_seconds()))
        duration_minutes = duration_seconds // 60

        tariff = self.get_tariff_for_category(category)
        if not tariff:
            # Fallback default tariff if not configured
            tariff = ParkingTariff(
                id=0, vehicle_category=category, base_duration_minutes=60,
                base_rate_cents=2000, hourly_rate_cents=1000, daily_max_cents=6000,
                grace_period_minutes=15, lost_ticket_fee_cents=5000
            )

        # 1. Grace period check
        if duration_minutes <= tariff.grace_period_minutes:
            gross_cents = 0
            reason = "Free Grace Period"
        else:
            # 2. Multi-day / daily calculation
            days = duration_minutes // 1440
            remaining_mins = duration_minutes % 1440

            day_charges = days * tariff.daily_max_cents

            # Intra-day charge
            if remaining_mins <= tariff.base_duration_minutes:
                intra_charge = tariff.base_rate_cents
            else:
                extra_mins = remaining_mins - tariff.base_duration_minutes
                extra_hours = math.ceil(extra_mins / 60.0)
                intra_charge = tariff.base_rate_cents + (extra_hours * tariff.hourly_rate_cents)

            # Cap intra-day charge at daily max
            if tariff.daily_max_cents > 0:
                intra_charge = min(intra_charge, tariff.daily_max_cents)

            gross_cents = day_charges + intra_charge
            reason = "Standard Parking Rate"

        # 3. Calculate Discount
        discount_info = AUTHORIZED_DISCOUNTS.get(discount_code, AUTHORIZED_DISCOUNTS["NONE"])
        pct = discount_info["pct"]
        if pct > 0:
            discount_cents = int(round((gross_cents * pct) / 100.0))
        else:
            discount_cents = min(gross_cents, custom_discount_cents)

        net_cents = max(0, gross_cents - discount_cents)

        return {
            "duration_minutes": duration_minutes,
            "duration_formatted": f"{duration_minutes // 60}h {duration_minutes % 60}m",
            "gross_cents": gross_cents,
            "discount_cents": discount_cents,
            "net_cents": net_cents,
            "discount_code": discount_code,
            "discount_name": discount_info["name"],
            "tariff": tariff,
            "tariff_snapshot": tariff.to_snapshot(),
            "reason": reason,
        }

    def find_active_session(self, identifier: str) -> Optional[ParkingSession]:
        """Look up active parking session by ticket number or registration number."""
        clean_id = identifier.strip().upper()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT ps.*, s.slot_code, z.name as zone_name
                FROM parking_sessions ps
                JOIN parking_slots s ON ps.slot_id = s.id
                JOIN parking_zones z ON s.zone_id = z.id
                WHERE (ps.ticket_number = ? OR ps.vehicle_registration = ?)
                  AND ps.status = 'ACTIVE'
                ORDER BY ps.id DESC LIMIT 1
            """, (clean_id, clean_id))
            row = cur.fetchone()
            if row:
                return ParkingSession.from_row(row)
            return None
        finally:
            conn.close()

    def process_exit_and_payment(self, session_id: int, payment_method: str = "CASH",
                                 discount_code: str = "NONE", custom_discount_cents: int = 0,
                                 cashier_id: Optional[int] = None,
                                 cashier_name: Optional[str] = None,
                                 notes: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Execute atomic checkout and payment transaction.
        TQM Guarantee:
        - Locks session and verifies still ACTIVE.
        - Calculates exact bill.
        - Records payment.
        - Marks session COMPLETED with full tariff snapshot.
        - Frees slot to AVAILABLE.
        - Writes immutable audit log.
        - All operations committed atomically or rolled back completely on error.
        """
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT ps.*, s.slot_code
                FROM parking_sessions ps
                JOIN parking_slots s ON ps.slot_id = s.id
                WHERE ps.id = ? AND ps.status = 'ACTIVE'
            """, (session_id,))
            session_row = cur.fetchone()
            if not session_row:
                return False, None, "Active parking session not found or already settled."

            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            bill = self.calculate_bill(
                entry_time_str=session_row["entry_time"],
                exit_time_str=now_iso,
                category=session_row["vehicle_category"],
                discount_code=discount_code,
                custom_discount_cents=custom_discount_cents
            )

            # 1. Update parking session
            cur.execute("""
                UPDATE parking_sessions
                SET status = 'COMPLETED',
                    exit_time = ?,
                    duration_minutes = ?,
                    gross_amount_cents = ?,
                    discount_cents = ?,
                    net_amount_cents = ?,
                    tariff_snapshot = ?,
                    discount_reason = ?,
                    notes = ?,
                    updated_at = ?
                WHERE id = ? AND status = 'ACTIVE'
            """, (
                now_iso,
                bill["duration_minutes"],
                bill["gross_cents"],
                bill["discount_cents"],
                bill["net_cents"],
                bill["tariff_snapshot"],
                bill["discount_name"],
                notes,
                now_iso,
                session_id
            ))
            if cur.rowcount == 0:
                conn.rollback()
                return False, None, "Session status changed concurrently. Operation aborted."

            # 2. Insert Payment Record
            txn_ref = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{session_id}"
            cur.execute("""
                INSERT INTO payments (
                    session_id, amount_cents, payment_method, payment_status,
                    transaction_reference, cashier_user_id, payment_time, created_at
                ) VALUES (?, ?, ?, 'PAID', ?, ?, ?, ?)
            """, (session_id, bill["net_cents"], payment_method, txn_ref, cashier_id, now_iso, now_iso))

            # 3. Release Parking Slot
            cur.execute("""
                UPDATE parking_slots
                SET status = 'AVAILABLE', updated_at = ?
                WHERE id = ?
            """, (now_iso, session_row["slot_id"]))

            # 4. Audit Log
            audit_service.log(
                action="VEHICLE_EXIT", entity_type="SESSION", entity_id=session_row["ticket_number"],
                details=f"Exit: Ticket #{session_row['ticket_number']} | Paid: ${bill['net_cents']/100:.2f} ({payment_method}) | Duration: {bill['duration_formatted']}",
                user_id=cashier_id, username=cashier_name, conn=conn
            )

            conn.commit()

            receipt_data = {
                "ticket_number": session_row["ticket_number"],
                "vehicle_registration": session_row["vehicle_registration"],
                "vehicle_category": session_row["vehicle_category"],
                "slot_code": session_row["slot_code"],
                "entry_time": session_row["entry_time"],
                "exit_time": now_iso,
                "duration_minutes": bill["duration_minutes"],
                "duration_formatted": bill["duration_formatted"],
                "gross_cents": bill["gross_cents"],
                "discount_cents": bill["discount_cents"],
                "discount_name": bill["discount_name"],
                "net_cents": bill["net_cents"],
                "payment_method": payment_method,
                "transaction_reference": txn_ref,
                "cashier_name": cashier_name or "Self-Service",
            }

            logger.info(f"Settled checkout: Ticket {session_row['ticket_number']}, Net ${bill['net_cents']/100:.2f}")
            return True, receipt_data, "Checkout and payment processed successfully. Slot released."

        except Exception as e:
            conn.rollback()
            logger.error(f"Billing transaction failed: {e}")
            return False, None, f"Payment transaction failed: {str(e)}"
        finally:
            conn.close()

billing_service = BillingService()
