"""
ParkSmart Pro — Parking Zone Domain Model
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ParkingZone:
    id: int
    code: str
    name: str
    floor_number: int
    description: Optional[str] = None
    is_active: bool = True
    total_slots: int = 0
    available_slots: int = 0
    occupied_slots: int = 0

    @classmethod
    def from_row(cls, row) -> "ParkingZone":
        keys = row.keys()
        return cls(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            floor_number=row["floor_number"],
            description=row["description"] if "description" in keys else None,
            is_active=bool(row["is_active"]) if "is_active" in keys else True,
            total_slots=row["total_slots"] if "total_slots" in keys else 0,
            available_slots=row["available_slots"] if "available_slots" in keys else 0,
            occupied_slots=row["occupied_slots"] if "occupied_slots" in keys else 0,
        )
