"""
ParkSmart Pro — Parking Reservation Domain Model
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Reservation:
    id: int
    reservation_code: str
    customer_name: str
    customer_phone: Optional[str]
    vehicle_registration: str
    vehicle_category: str
    slot_id: int
    slot_code: Optional[str]
    zone_name: Optional[str]
    start_time: str
    end_time: str
    status: str = "CONFIRMED"  # CONFIRMED, CHECKED_IN, CANCELLED, EXPIRED
    notes: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Reservation":
        keys = row.keys()
        return cls(
            id=row["id"],
            reservation_code=row["reservation_code"],
            customer_name=row["customer_name"],
            customer_phone=row["customer_phone"] if "customer_phone" in keys else None,
            vehicle_registration=row["vehicle_registration"],
            vehicle_category=row["vehicle_category"],
            slot_id=row["slot_id"],
            slot_code=row["slot_code"] if "slot_code" in keys else None,
            zone_name=row["zone_name"] if "zone_name" in keys else None,
            start_time=row["start_time"],
            end_time=row["end_time"],
            status=row["status"],
            notes=row["notes"] if "notes" in keys else None,
            created_by_user_id=row["created_by_user_id"] if "created_by_user_id" in keys else None,
            created_at=row["created_at"] if "created_at" in keys else None,
        )
