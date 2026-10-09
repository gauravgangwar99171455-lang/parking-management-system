"""
ParkSmart Pro — Parking Session Domain Model
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ParkingSession:
    id: int
    ticket_number: str
    vehicle_registration: str
    vehicle_category: str
    slot_id: int
    slot_code: Optional[str] = None
    zone_name: Optional[str] = None
    entry_time: str = ""
    exit_time: Optional[str] = None
    status: str = "ACTIVE"  # ACTIVE, COMPLETED, CANCELLED
    duration_minutes: int = 0
    gross_amount_cents: int = 0
    discount_cents: int = 0
    net_amount_cents: int = 0
    tariff_snapshot: Optional[str] = None
    discount_reason: Optional[str] = None
    notes: Optional[str] = None
    created_by_user_id: Optional[int] = None
    payment_method: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "ParkingSession":
        keys = row.keys()
        return cls(
            id=row["id"],
            ticket_number=row["ticket_number"],
            vehicle_registration=row["vehicle_registration"],
            vehicle_category=row["vehicle_category"],
            slot_id=row["slot_id"],
            slot_code=row["slot_code"] if "slot_code" in keys else None,
            zone_name=row["zone_name"] if "zone_name" in keys else None,
            entry_time=row["entry_time"],
            exit_time=row["exit_time"] if "exit_time" in keys else None,
            status=row["status"],
            duration_minutes=row["duration_minutes"] if "duration_minutes" in keys else 0,
            gross_amount_cents=row["gross_amount_cents"] if "gross_amount_cents" in keys else 0,
            discount_cents=row["discount_cents"] if "discount_cents" in keys else 0,
            net_amount_cents=row["net_amount_cents"] if "net_amount_cents" in keys else 0,
            tariff_snapshot=row["tariff_snapshot"] if "tariff_snapshot" in keys else None,
            discount_reason=row["discount_reason"] if "discount_reason" in keys else None,
            notes=row["notes"] if "notes" in keys else None,
            created_by_user_id=row["created_by_user_id"] if "created_by_user_id" in keys else None,
            payment_method=row["payment_method"] if "payment_method" in keys else None,
            created_at=row["created_at"] if "created_at" in keys else None,
        )

    def is_active(self) -> bool:
        return self.status == "ACTIVE"
