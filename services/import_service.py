"""
ParkSmart Pro — Robust CSV Import & Validation Engine
TQM Principle: Prevention, Rigorous Pre-Validation & Atomic Execution
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from database.connection import get_db_connection
from utils.export_helpers import read_csv_records
from utils.validators import validate_slot_code, validate_reg_number, validate_iso_datetime
from services.audit_service import audit_service
from utils.logger import get_logger

logger = get_logger("import_service")

SLOT_REQUIRED_COLUMNS = ["slot_code", "zone_code", "supported_category"]
HISTORICAL_REQUIRED_COLUMNS = ["ticket_number", "vehicle_registration", "vehicle_category", "slot_code", "entry_time", "exit_time", "net_amount_cents"]
RESERVATION_REQUIRED_COLUMNS = ["customer_name", "customer_phone", "vehicle_registration", "vehicle_category", "slot_code", "start_time", "end_time"]

class ImportService:
    def validate_slot_csv(self, filepath: Path) -> Dict[str, Any]:
        """
        Validate CSV of Parking Slots against database constraints.
        Returns preview data, valid rows, invalid rows with specific error diagnostics.
        """
        success, headers, records, msg = read_csv_records(filepath)
        if not success:
            return {"success": False, "error": msg}

        missing = [c for c in SLOT_REQUIRED_COLUMNS if c not in headers]
        if missing:
            return {
                "success": False,
                "error": f"Missing mandatory columns: {', '.join(missing)}. Required: {', '.join(SLOT_REQUIRED_COLUMNS)}"
            }

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            # Fetch existing slot codes and zone codes
            cur.execute("SELECT slot_code FROM parking_slots")
            existing_slots = {r["slot_code"] for r in cur.fetchall()}

            cur.execute("SELECT id, code FROM parking_zones WHERE is_active = 1")
            zone_map = {r["code"]: r["id"] for r in cur.fetchall()}

            valid_categories = {"TWO_WHEELER", "CAR", "SUV", "COMMERCIAL", "EV"}

            valid_rows = []
            invalid_rows = []
            seen_in_file = set()

            for idx, row in enumerate(records, start=2): # 1-based, row 1 is header
                slot_code = row.get("slot_code", "").strip().upper()
                zone_code = row.get("zone_code", "").strip().upper()
                category = row.get("supported_category", "").strip().upper()

                errors = []
                # Validate slot code
                is_ok, slot_err = validate_slot_code(slot_code)
                if not is_ok:
                    errors.append(slot_err)
                elif slot_code in existing_slots:
                    errors.append(f"Slot code '{slot_code}' already exists in database.")
                elif slot_code in seen_in_file:
                    errors.append(f"Duplicate slot code '{slot_code}' in CSV file.")

                # Validate zone
                if zone_code not in zone_map:
                    errors.append(f"Zone code '{zone_code}' does not exist.")

                # Validate category
                if category not in valid_categories:
                    errors.append(f"Invalid category '{category}'. Allowed: {', '.join(sorted(valid_categories))}")

                if errors:
                    invalid_rows.append({
                        "row_number": idx,
                        "data": row,
                        "reasons": "; ".join(errors)
                    })
                else:
                    seen_in_file.add(slot_code)
                    valid_rows.append({
                        "row_number": idx,
                        "slot_code": slot_code,
                        "zone_id": zone_map[zone_code],
                        "zone_code": zone_code,
                        "supported_category": category,
                        "status": "AVAILABLE"
                    })

            return {
                "success": True,
                "total_rows": len(records),
                "valid_count": len(valid_rows),
                "invalid_count": len(invalid_rows),
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows,
                "headers": headers,
            }
        finally:
            conn.close()

    def commit_slot_import(self, valid_rows: List[Dict[str, Any]], filename: str,
                           user_id: Optional[int] = None, username: Optional[str] = None) -> Tuple[bool, str]:
        """Atomically insert validated slot rows."""
        if not valid_rows:
            return False, "No valid rows to import."

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            data_to_insert = [
                (r["slot_code"], r["zone_id"], r["supported_category"], "AVAILABLE")
                for r in valid_rows
            ]
            cur.executemany("""
                INSERT INTO parking_slots (slot_code, zone_id, supported_category, status)
                VALUES (?, ?, ?, ?)
            """, data_to_insert)

            # Record import log
            cur.execute("""
                INSERT INTO import_logs (
                    import_type, filename, total_rows, successful_rows, failed_rows, error_summary, user_id
                ) VALUES ('PARKING_SLOTS', ?, ?, ?, 0, 'Clean batch import', ?)
            """, (filename, len(valid_rows), len(valid_rows), user_id))

            audit_service.log(
                action="IMPORT_SLOTS", entity_type="IMPORT", entity_id=filename,
                details=f"Imported {len(valid_rows)} parking slots from {filename}",
                user_id=user_id, username=username, conn=conn
            )
            conn.commit()
            return True, f"Successfully imported {len(valid_rows)} parking slots."
        except Exception as e:
            conn.rollback()
            logger.error(f"Slot import rollback: {e}")
            return False, f"Import transaction failed: {str(e)}"
        finally:
            conn.close()

    def validate_historical_sessions_csv(self, filepath: Path) -> Dict[str, Any]:
        """Validate historical completed parking sessions CSV."""
        success, headers, records, msg = read_csv_records(filepath)
        if not success:
            return {"success": False, "error": msg}

        missing = [c for c in HISTORICAL_REQUIRED_COLUMNS if c not in headers]
        if missing:
            return {
                "success": False,
                "error": f"Missing mandatory columns: {', '.join(missing)}."
            }

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, slot_code FROM parking_slots")
            slot_map = {r["slot_code"]: r["id"] for r in cur.fetchall()}

            cur.execute("SELECT ticket_number FROM parking_sessions")
            existing_tickets = {r["ticket_number"] for r in cur.fetchall()}

            valid_categories = {"TWO_WHEELER", "CAR", "SUV", "COMMERCIAL", "EV"}

            valid_rows = []
            invalid_rows = []
            seen_tickets = set()

            for idx, row in enumerate(records, start=2):
                ticket_no = row.get("ticket_number", "").strip().upper()
                reg_no = row.get("vehicle_registration", "").strip().upper()
                category = row.get("vehicle_category", "").strip().upper()
                slot_code = row.get("slot_code", "").strip().upper()
                entry_time = row.get("entry_time", "").strip()
                exit_time = row.get("exit_time", "").strip()
                net_str = row.get("net_amount_cents", "0").strip()

                errors = []
                if not ticket_no:
                    errors.append("Ticket number cannot be empty.")
                elif ticket_no in existing_tickets:
                    errors.append(f"Ticket #{ticket_no} already exists in database.")
                elif ticket_no in seen_tickets:
                    errors.append(f"Duplicate ticket #{ticket_no} in CSV.")

                is_ok_reg, reg_err = validate_reg_number(reg_no)
                if not is_ok_reg:
                    errors.append(reg_err)

                if category not in valid_categories:
                    errors.append(f"Invalid category '{category}'.")

                if slot_code not in slot_map:
                    errors.append(f"Slot code '{slot_code}' not found in database.")

                ok_entry, dt_entry, err_entry = validate_iso_datetime(entry_time)
                if not ok_entry:
                    errors.append(f"Entry time invalid: {err_entry}")

                ok_exit, dt_exit, err_exit = validate_iso_datetime(exit_time)
                if not ok_exit:
                    errors.append(f"Exit time invalid: {err_exit}")

                if ok_entry and ok_exit and dt_exit < dt_entry:
                    errors.append("Exit time cannot be earlier than entry time.")

                try:
                    net_cents = int(float(net_str))
                    if net_cents < 0:
                        errors.append("Net amount cannot be negative.")
                except ValueError:
                    errors.append(f"Invalid net amount '{net_str}'.")
                    net_cents = 0

                if errors:
                    invalid_rows.append({
                        "row_number": idx,
                        "data": row,
                        "reasons": "; ".join(errors)
                    })
                else:
                    seen_tickets.add(ticket_no)
                    dur_mins = int((dt_exit - dt_entry).total_seconds()) // 60 if (ok_entry and ok_exit) else 0
                    valid_rows.append({
                        "ticket_number": ticket_no,
                        "vehicle_registration": reg_no,
                        "vehicle_category": category,
                        "slot_id": slot_map[slot_code],
                        "entry_time": dt_entry.strftime("%Y-%m-%d %H:%M:%S"),
                        "exit_time": dt_exit.strftime("%Y-%m-%d %H:%M:%S"),
                        "duration_minutes": dur_mins,
                        "gross_amount_cents": net_cents,
                        "discount_cents": 0,
                        "net_amount_cents": net_cents,
                        "status": "COMPLETED",
                        "notes": "Imported historical session"
                    })

            return {
                "success": True,
                "total_rows": len(records),
                "valid_count": len(valid_rows),
                "invalid_count": len(invalid_rows),
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows,
                "headers": headers,
            }
        finally:
            conn.close()

    def commit_historical_import(self, valid_rows: List[Dict[str, Any]], filename: str,
                                 user_id: Optional[int] = None, username: Optional[str] = None) -> Tuple[bool, str]:
        """Atomically import historical sessions and their matching payments."""
        if not valid_rows:
            return False, "No valid records to import."

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sessions_data = [
                (
                    r["ticket_number"], r["vehicle_registration"], r["vehicle_category"],
                    r["slot_id"], r["entry_time"], r["exit_time"], r["status"],
                    r["duration_minutes"], r["gross_amount_cents"], r["discount_cents"],
                    r["net_amount_cents"], r["notes"]
                )
                for r in valid_rows
            ]

            cur.executemany("""
                INSERT INTO parking_sessions (
                    ticket_number, vehicle_registration, vehicle_category, slot_id,
                    entry_time, exit_time, status, duration_minutes, gross_amount_cents,
                    discount_cents, net_amount_cents, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sessions_data)

            # Record import log
            cur.execute("""
                INSERT INTO import_logs (
                    import_type, filename, total_rows, successful_rows, failed_rows, error_summary, user_id
                ) VALUES ('HISTORICAL_SESSIONS', ?, ?, ?, 0, 'Clean batch import', ?)
            """, (filename, len(valid_rows), len(valid_rows), user_id))

            audit_service.log(
                action="IMPORT_HISTORICAL", entity_type="IMPORT", entity_id=filename,
                details=f"Imported {len(valid_rows)} historical sessions from {filename}",
                user_id=user_id, username=username, conn=conn
            )
            conn.commit()
            return True, f"Successfully imported {len(valid_rows)} historical records."
        except Exception as e:
            conn.rollback()
            logger.error(f"Historical import rollback: {e}")
            return False, f"Import transaction failed: {str(e)}"
        finally:
            conn.close()

import_service = ImportService()
