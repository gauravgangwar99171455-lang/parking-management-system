"""
ParkSmart Pro — Parking Slot Domain Model
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ParkingSlot:
    id: int
    slot_code: str
    zone_id: int
    zone_name: Optional[str] = None
    zone_code: Optional[str] = None
    floor_number: int = 0
    supported_category: str = "CAR"
    status: str = "AVAILABLE"  # AVAILABLE, OCCUPIED, RESERVED, MAINTENANCE
    is_active: bool = True
    current_ticket: Optional[str] = None
    current_vehicle: Optional[str] = None
    current_entry_time: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "ParkingSlot":
        keys = row.keys()
        return cls(
            id=row["id"],
            slot_code=row["slot_code"],
            zone_id=row["zone_id"],
            zone_name=row["zone_name"] if "zone_name" in keys else None,
            zone_code=row["zone_code"] if "zone_code" in keys else None,
            floor_number=row["floor_number"] if "floor_number" in keys else 0,
            supported_category=row["supported_category"],
            status=row["status"],
            is_active=bool(row["is_active"]) if "is_active" in keys else True,
            current_ticket=row["current_ticket"] if "current_ticket" in keys else None,
            current_vehicle=row["current_vehicle"] if "current_vehicle" in keys else None,
            current_entry_time=row["current_entry_time"] if "current_entry_time" in keys else None,
        )

    def is_available(self) -> bool:
        return self.is_active and self.status == "AVAILABLE"
