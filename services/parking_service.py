"""
ParkSmart Pro — Parking Management Service
TQM Principle: Zero Defects, ACID Transactions & Invariant Protection
"""

import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from database.connection import get_db_connection
from models.parking_slot import ParkingSlot
from models.parking_zone import ParkingZone
from models.parking_session import ParkingSession
from services.audit_service import audit_service
from utils.validators import validate_reg_number, sanitize_reg_number
from utils.logger import get_logger

logger = get_logger("parking_service")

class ParkingService:
    def get_zones(self, active_only: bool = True) -> List[ParkingZone]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT z.*,
                       COUNT(s.id) as total_slots,
                       SUM(CASE WHEN s.status = 'AVAILABLE' AND s.is_active = 1 THEN 1 ELSE 0 END) as available_slots,
                       SUM(CASE WHEN s.status = 'OCCUPIED' AND s.is_active = 1 THEN 1 ELSE 0 END) as occupied_slots
                FROM parking_zones z
                LEFT JOIN parking_slots s ON z.id = s.zone_id
            """
            if active_only:
                query += " WHERE z.is_active = 1"
            query += " GROUP BY z.id ORDER BY z.floor_number ASC, z.code ASC"
            cur.execute(query)
            return [ParkingZone.from_row(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_slots(self, zone_id: Optional[int] = None, floor_number: Optional[int] = None,
                  category: Optional[str] = None, status: Optional[str] = None,
                  search_code: Optional[str] = None) -> List[ParkingSlot]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT s.*, z.name as zone_name, z.code as zone_code, z.floor_number,
                       ps.ticket_number as current_ticket,
                       ps.vehicle_registration as current_vehicle,
                       ps.entry_time as current_entry_time
                FROM parking_slots s
                JOIN parking_zones z ON s.zone_id = z.id
                LEFT JOIN parking_sessions ps ON s.id = ps.slot_id AND ps.status = 'ACTIVE'
                WHERE 1=1
            """
            params = []
            if zone_id:
                query += " AND s.zone_id = ?"
                params.append(zone_id)
            if floor_number is not None:
                query += " AND z.floor_number = ?"
                params.append(floor_number)
            if category and category != "ALL":
                query += " AND s.supported_category = ?"
                params.append(category)
            if status and status != "ALL":
                query += " AND s.status = ?"
                params.append(status)
            if search_code:
                query += " AND s.slot_code LIKE ?"
                params.append(f"%{search_code.strip()}%")

            query += " ORDER BY z.floor_number ASC, s.slot_code ASC"
            cur.execute(query, params)
            return [ParkingSlot.from_row(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def add_slot(self, slot_code: str, zone_id: int, category: str) -> Tuple[bool, str]:
        slot_code = slot_code.strip().upper()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO parking_slots (slot_code, zone_id, supported_category, status)
                VALUES (?, ?, ?, 'AVAILABLE')
            """, (slot_code, zone_id, category))
            conn.commit()
            audit_service.log(
                action="ADD_SLOT", entity_type="SLOT", entity_id=slot_code,
                details=f"Created slot {slot_code} in zone {zone_id} ({category})"
            )
            return True, f"Slot {slot_code} added successfully."
        except Exception as e:
            conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                return False, f"Slot code '{slot_code}' already exists."
            return False, f"Failed to add slot: {str(e)}"
        finally:
            conn.close()

    def update_slot_status(self, slot_id: int, new_status: str, notes: str = "") -> Tuple[bool, str]:
        valid_statuses = ("AVAILABLE", "OCCUPIED", "RESERVED", "MAINTENANCE")
        if new_status not in valid_statuses:
            return False, f"Invalid status: {new_status}"

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT slot_code, status FROM parking_slots WHERE id = ?", (slot_id,))
            row = cur.fetchone()
            if not row:
                return False, "Slot not found."
            
            # If changing away from OCCUPIED, check if active session exists
            if row["status"] == "OCCUPIED" and new_status != "OCCUPIED":
                cur.execute("SELECT ticket_number FROM parking_sessions WHERE slot_id = ? AND status = 'ACTIVE'", (slot_id,))
                active = cur.fetchone()
                if active:
                    return False, f"Cannot change status: Slot is currently occupied by active ticket {active['ticket_number']}."

            cur.execute("""
                UPDATE parking_slots
                SET status = ?, updated_at = DATETIME('now', 'localtime')
                WHERE id = ?
            """, (new_status, slot_id))
            conn.commit()

            audit_service.log(
                action="UPDATE_SLOT_STATUS", entity_type="SLOT", entity_id=row["slot_code"],
                details=f"Status changed from {row['status']} to {new_status}. {notes}"
            )
            return True, f"Slot {row['slot_code']} status updated to {new_status}."
        finally:
            conn.close()

    def find_eligible_slots(self, category: str, zone_id: Optional[int] = None) -> List[ParkingSlot]:
        """Find all currently AVAILABLE slots capable of parking the given vehicle category."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT s.*, z.name as zone_name, z.code as zone_code, z.floor_number
                FROM parking_slots s
                JOIN parking_zones z ON s.zone_id = z.id
                WHERE s.status = 'AVAILABLE' AND s.is_active = 1 AND s.supported_category = ?
            """
            params = [category]
            if zone_id:
                query += " AND s.zone_id = ?"
                params.append(zone_id)
            query += " ORDER BY z.floor_number ASC, s.slot_code ASC"
            cur.execute(query, params)
            return [ParkingSlot.from_row(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def register_vehicle_entry(self, vehicle_reg: str, category: str,
                               slot_id: Optional[int] = None,
                               user_id: Optional[int] = None,
                               username: Optional[str] = None,
                               notes: Optional[str] = None) -> Tuple[bool, Optional[ParkingSession], str]:
        """
        Register a new vehicle entry atomically.
        Guarantees:
        1. Reg number is valid.
        2. No active parking session exists for this vehicle.
        3. Slot is genuinely AVAILABLE and supports this category.
        4. Updates slot to OCCUPIED and creates session in single transaction.
        """
        is_valid, msg = validate_reg_number(vehicle_reg)
        if not is_valid:
            return False, None, msg
        clean_reg = sanitize_reg_number(vehicle_reg)

        conn = get_db_connection()
        try:
            cur = conn.cursor()

            # 1. Check for existing active session for this vehicle
            cur.execute("""
                SELECT ticket_number, slot_id FROM parking_sessions
                WHERE vehicle_registration = ? AND status = 'ACTIVE'
            """, (clean_reg,))
            existing = cur.fetchone()
            if existing:
                return False, None, f"Vehicle '{clean_reg}' is already parked inside under Ticket #{existing['ticket_number']}."

            # 2. Select slot
            if slot_id is None:
                # Auto-assign first available slot
                cur.execute("""
                    SELECT id, slot_code FROM parking_slots
                    WHERE status = 'AVAILABLE' AND is_active = 1 AND supported_category = ?
                    ORDER BY id ASC LIMIT 1
                """, (category,))
                slot_row = cur.fetchone()
                if not slot_row:
                    return False, None, f"No available slots found for vehicle category '{category}'."
                chosen_slot_id = slot_row["id"]
                chosen_slot_code = slot_row["slot_code"]
            else:
                cur.execute("""
                    SELECT id, slot_code, status, is_active, supported_category
                    FROM parking_slots WHERE id = ?
                """, (slot_id,))
                slot_row = cur.fetchone()
                if not slot_row:
                    return False, None, "Selected slot does not exist."
                if not slot_row["is_active"] or slot_row["status"] != "AVAILABLE":
                    return False, None, f"Slot {slot_row['slot_code']} is not available (Current status: {slot_row['status']})."
                if slot_row["supported_category"] != category:
                    return False, None, f"Slot {slot_row['slot_code']} is reserved for '{slot_row['supported_category']}', not '{category}'."
                chosen_slot_id = slot_row["id"]
                chosen_slot_code = slot_row["slot_code"]

            # 3. Generate unique ticket number
            today_str = datetime.now().strftime("%Y%m%d")
            rand_suffix = uuid.uuid4().hex[:6].upper()
            ticket_number = f"TKT-{today_str}-{rand_suffix}"
            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 4. Atomic Execution: Update slot + insert session
            cur.execute("""
                UPDATE parking_slots
                SET status = 'OCCUPIED', updated_at = ?
                WHERE id = ? AND status = 'AVAILABLE'
            """, (now_iso, chosen_slot_id))
            if cur.rowcount == 0:
                conn.rollback()
                return False, None, f"Slot {chosen_slot_code} was allocated to another vehicle simultaneously. Please retry."

            cur.execute("""
                INSERT INTO parking_sessions (
                    ticket_number, vehicle_registration, vehicle_category, slot_id,
                    entry_time, status, notes, created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?)
            """, (ticket_number, clean_reg, category, chosen_slot_id, now_iso, notes, user_id, now_iso, now_iso))

            session_id = cur.lastrowid

            # Audit logging within same transaction
            audit_service.log(
                action="VEHICLE_ENTRY", entity_type="SESSION", entity_id=ticket_number,
                details=f"Entry: {clean_reg} ({category}) in Slot {chosen_slot_code}",
                user_id=user_id, username=username, conn=conn
            )

            conn.commit()

            # Retrieve created session object
            cur.execute("""
                SELECT ps.*, s.slot_code, z.name as zone_name
                FROM parking_sessions ps
                JOIN parking_slots s ON ps.slot_id = s.id
                JOIN parking_zones z ON s.zone_id = z.id
                WHERE ps.id = ?
            """, (session_id,))
            session_obj = ParkingSession.from_row(cur.fetchone())

            logger.info(f"Registered entry: Ticket {ticket_number}, Vehicle {clean_reg}, Slot {chosen_slot_code}")
            return True, session_obj, f"Entry ticket {ticket_number} generated successfully for slot {chosen_slot_code}."

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to register vehicle entry: {e}")
            if "idx_unique_active_session" in str(e):
                return False, None, f"Integrity Constraint: Vehicle '{clean_reg}' already has an active session."
            if "idx_unique_active_slot_alloc" in str(e):
                return False, None, "Integrity Constraint: Slot already assigned to an active session."
            return False, None, f"Database transaction failed: {str(e)}"
        finally:
            conn.close()

parking_service = ParkingService()
