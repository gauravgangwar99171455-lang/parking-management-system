"""
ParkSmart Pro — Parking Tariff Domain Model
"""

from dataclasses import dataclass
import json

@dataclass
class ParkingTariff:
    id: int
    vehicle_category: str
    base_duration_minutes: int
    base_rate_cents: int
    hourly_rate_cents: int
    daily_max_cents: int
    grace_period_minutes: int
    lost_ticket_fee_cents: int
    is_active: bool = True

    @classmethod
    def from_row(cls, row) -> "ParkingTariff":
        return cls(
            id=row["id"],
            vehicle_category=row["vehicle_category"],
            base_duration_minutes=row["base_duration_minutes"],
            base_rate_cents=row["base_rate_cents"],
            hourly_rate_cents=row["hourly_rate_cents"],
            daily_max_cents=row["daily_max_cents"],
            grace_period_minutes=row["grace_period_minutes"],
            lost_ticket_fee_cents=row["lost_ticket_fee_cents"],
            is_active=bool(row["is_active"]),
        )

    def to_snapshot(self) -> str:
        """Serialize tariff rates into JSON for immutable session snapshots."""
        return json.dumps({
            "tariff_id": self.id,
            "vehicle_category": self.vehicle_category,
            "base_duration_minutes": self.base_duration_minutes,
            "base_rate_cents": self.base_rate_cents,
            "hourly_rate_cents": self.hourly_rate_cents,
            "daily_max_cents": self.daily_max_cents,
            "grace_period_minutes": self.grace_period_minutes,
            "lost_ticket_fee_cents": self.lost_ticket_fee_cents,
        })
