"""
ParkSmart Pro — Data Validation Utilities
TQM Principle: Prevention Rather Than Correction
All inputs are validated and sanitized before touching domain models or database transactions.
"""

import re
from datetime import datetime
from typing import Tuple, Optional

# Regex patterns
RE_VEHICLE_REG = re.compile(r"^[A-Z0-9\-\s]{3,15}$", re.IGNORECASE)
RE_SLOT_CODE = re.compile(r"^[A-Z0-9]{1,4}[-]?[A-Z0-9]{1,4}$", re.IGNORECASE)
RE_TICKET_NO = re.compile(r"^TKT-\d{8}-[A-Z0-9]{4,10}$", re.IGNORECASE)
RE_USERNAME = re.compile(r"^[a-zA-Z0-9_]{3,20}$")

def sanitize_reg_number(reg_no: str) -> str:
    """Sanitize and normalize vehicle registration numbers (e.g., 'ka 01 ab 1234' -> 'KA-01-AB-1234' or uppercase alphanumeric)."""
    if not reg_no:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", reg_no).upper()
    return cleaned

def validate_reg_number(reg_no: str) -> Tuple[bool, str]:
    """Validate vehicle registration number."""
    if not reg_no or not reg_no.strip():
        return False, "Registration number cannot be empty."
    cleaned = sanitize_reg_number(reg_no)
    if len(cleaned) < 3:
        return False, "Registration number too short (minimum 3 characters)."
    if len(cleaned) > 15:
        return False, "Registration number too long (maximum 15 characters)."
    if not cleaned.isalnum():
        return False, "Registration number must contain only letters and numbers."
    return True, ""

def validate_slot_code(slot_code: str) -> Tuple[bool, str]:
    """Validate parking slot identifier."""
    if not slot_code or not slot_code.strip():
        return False, "Slot code cannot be empty."
    slot_code = slot_code.strip().upper()
    if not RE_SLOT_CODE.match(slot_code):
        return False, "Slot code must be in format like A-101, B2-05, or L1-01 (letters, numbers, hyphen)."
    return True, ""

def validate_ticket_number(ticket_no: str) -> Tuple[bool, str]:
    """Validate ticket number format."""
    if not ticket_no or not ticket_no.strip():
        return False, "Ticket number cannot be empty."
    ticket_no = ticket_no.strip().upper()
    if not RE_TICKET_NO.match(ticket_no) and len(ticket_no) < 6:
        return False, "Invalid ticket format. Expected format: TKT-YYYYMMDD-XXXX."
    return True, ""

def validate_iso_datetime(dt_str: str) -> Tuple[bool, Optional[datetime], str]:
    """Validate ISO 8601 datetime string."""
    if not dt_str:
        return False, None, "Datetime string cannot be empty."
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(dt_str.strip(), fmt)
            return True, parsed, ""
        except ValueError:
            continue
    return False, None, f"Invalid datetime format: '{dt_str}'. Expected 'YYYY-MM-DD HH:MM:SS'."

def validate_positive_amount(val) -> Tuple[bool, int, str]:
    """
    Validate that an amount is a positive number and convert to minor units (e.g. 10.50 -> 1050).
    """
    try:
        f_val = float(val)
        if f_val < 0:
            return False, 0, "Amount cannot be negative."
        minor_units = int(round(f_val * 100))
        return True, minor_units, ""
    except (ValueError, TypeError):
        return False, 0, f"Invalid numeric amount: '{val}'."

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username."""
    if not username:
        return False, "Username cannot be empty."
    if not RE_USERNAME.match(username):
        return False, "Username must be 3-20 characters long and contain only letters, numbers, and underscores."
    return True, ""

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password strength."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""
