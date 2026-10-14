"""
ParkSmart Pro — Parking Reservation Service
TQM Principle: Conflict Prevention & Schedule Integrity
"""

import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from database.connection import get_db_connection
from models.reservation import Reservation
from services.audit_service import audit_service
from utils.validators import validate_reg_number, sanitize_reg_number, validate_iso_datetime
from utils.logger import get_logger

logger = get_logger("reservation_service")

class ReservationService:
    def check_slot_availability(self, slot_id: int, start_time_str: str, end_time_str: str,
                                exclude_reservation_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Check if slot is free from overlapping reservations during [start_time, end_time].
        Overlapping condition: existing.start_time < new.end_time AND existing.end_time > new.start_time
        """
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            # 1. Check if slot exists and is active
            cur.execute("SELECT slot_code, is_active FROM parking_slots WHERE id = ?", (slot_id,))
            slot = cur.fetchone()
            if not slot or not slot["is_active"]:
                return False, "Parking slot is invalid or inactive."

            # 2. Check for overlapping CONFIRMED reservations
            query = """
                SELECT id, reservation_code, start_time, end_time
                FROM reservations
                WHERE slot_id = ?
                  AND status = 'CONFIRMED'
                  AND start_time < ?
                  AND end_time > ?
            """
            params = [slot_id, end_time_str, start_time_str]
            if exclude_reservation_id:
                query += " AND id != ?"
                params.append(exclude_reservation_id)

            cur.execute(query, params)
            conflict = cur.fetchone()
            if conflict:
                return False, f"Slot {slot['slot_code']} is already reserved by #{conflict['reservation_code']} ({conflict['start_time']} to {conflict['end_time']})."

            return True, "Slot is available."
        finally:
            conn.close()

    def create_reservation(self, customer_name: str, customer_phone: str, vehicle_reg: str,
                           category: str, slot_id: int, start_time_str: str, end_time_str: str,
                           user_id: Optional[int] = None, username: Optional[str] = None,
                           notes: Optional[str] = None) -> Tuple[bool, Optional[Reservation], str]:
        """Create a new parking reservation safely."""
        if not customer_name.strip():
            return False, None, "Customer name is required."

        is_reg_valid, reg_msg = validate_reg_number(vehicle_reg)
        if not is_reg_valid:
            return False, None, reg_msg
        clean_reg = sanitize_reg_number(vehicle_reg)

        valid_s, dt_start, msg_s = validate_iso_datetime(start_time_str)
        if not valid_s:
            return False, None, f"Invalid start time: {msg_s}"
        valid_e, dt_end, msg_e = validate_iso_datetime(end_time_str)
        if not valid_e:
            return False, None, f"Invalid end time: {msg_e}"

        if dt_end <= dt_start:
            return False, None, "End time must be after start time."

        iso_start = dt_start.strftime("%Y-%m-%d %H:%M:%S")
        iso_end = dt_end.strftime("%Y-%m-%d %H:%M:%S")

        # Check slot conflict
        is_free, reason = self.check_slot_availability(slot_id, iso_start, iso_end)
        if not is_free:
            return False, None, reason

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            # Verify vehicle category compatibility
            cur.execute("SELECT slot_code, supported_category FROM parking_slots WHERE id = ?", (slot_id,))
            s_row = cur.fetchone()
            if s_row["supported_category"] != category:
                return False, None, f"Slot {s_row['slot_code']} supports '{s_row['supported_category']}', cannot book for '{category}'."

            res_code = f"RES-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cur.execute("""
                INSERT INTO reservations (
                    reservation_code, customer_name, customer_phone, vehicle_registration,
                    vehicle_category, slot_id, start_time, end_time, status, notes,
                    created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?, ?, ?, ?)
            """, (res_code, customer_name.strip(), customer_phone.strip(), clean_reg,
                  category, slot_id, iso_start, iso_end, notes, user_id, now_iso, now_iso))
            
            res_id = cur.lastrowid

            audit_service.log(
                action="CREATE_RESERVATION", entity_type="RESERVATION", entity_id=res_code,
                details=f"Booked Slot {s_row['slot_code']} for {clean_reg} ({iso_start} - {iso_end})",
                user_id=user_id, username=username, conn=conn
            )
            conn.commit()

            cur.execute("""
                SELECT r.*, s.slot_code, z.name as zone_name
                FROM reservations r
                JOIN parking_slots s ON r.slot_id = s.id
                JOIN parking_zones z ON s.zone_id = z.id
                WHERE r.id = ?
            """, (res_id,))
            res_obj = Reservation.from_row(cur.fetchone())

            logger.info(f"Reservation created: #{res_code} for {clean_reg} in {s_row['slot_code']}")
            return True, res_obj, f"Reservation #{res_code} confirmed successfully."

        except Exception as e:
            conn.rollback()
            return False, None, f"Database transaction failed: {str(e)}"
        finally:
            conn.close()

    def cancel_reservation(self, reservation_id: int, user_id: Optional[int] = None,
                           username: Optional[str] = None, reason: str = "") -> Tuple[bool, str]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT reservation_code, status, slot_id FROM reservations WHERE id = ?", (reservation_id,))
            res = cur.fetchone()
            if not res:
                return False, "Reservation not found."
            if res["status"] != "CONFIRMED":
                return False, f"Cannot cancel: reservation is already {res['status']}."

            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                UPDATE reservations
                SET status = 'CANCELLED', updated_at = ?
                WHERE id = ?
            """, (now_iso, reservation_id))

            # If slot was marked RESERVED, set back to AVAILABLE
            cur.execute("""
                UPDATE parking_slots
                SET status = 'AVAILABLE', updated_at = ?
                WHERE id = ? AND status = 'RESERVED'
            """, (now_iso, res["slot_id"]))

            audit_service.log(
                action="CANCEL_RESERVATION", entity_type="RESERVATION", entity_id=res["reservation_code"],
                details=f"Cancelled: #{res['reservation_code']}. Reason: {reason}",
                user_id=user_id, username=username, conn=conn
            )
            conn.commit()
            return True, f"Reservation #{res['reservation_code']} cancelled."
        finally:
            conn.close()

    def get_reservations(self, status: Optional[str] = None, search: Optional[str] = None) -> List[Reservation]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT r.*, s.slot_code, z.name as zone_name
                FROM reservations r
                JOIN parking_slots s ON r.slot_id = s.id
                JOIN parking_zones z ON s.zone_id = z.id
                WHERE 1=1
            """
            params = []
            if status and status != "ALL":
                query += " AND r.status = ?"
                params.append(status)
            if search:
                query += " AND (r.reservation_code LIKE ? OR r.vehicle_registration LIKE ? OR r.customer_name LIKE ?)"
                kw = f"%{search.strip()}%"
                params.extend([kw, kw, kw])

            query += " ORDER BY r.start_time DESC"
            cur.execute(query, params)
            return [Reservation.from_row(r) for r in cur.fetchall()]
        finally:
            conn.close()

reservation_service = ReservationService()
