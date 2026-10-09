"""
ParkSmart Pro — Payment and Audit Log Domain Models
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Payment:
    id: int
    session_id: int
    amount_cents: int
    payment_method: str  # CASH, CARD, UPI, WALLET, WAIVED
    payment_status: str  # PAID, REFUNDED, FAILED
    transaction_reference: Optional[str] = None
    cashier_user_id: Optional[int] = None
    cashier_name: Optional[str] = None
    payment_time: str = ""

    @classmethod
    def from_row(cls, row) -> "Payment":
        keys = row.keys()
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            amount_cents=row["amount_cents"],
            payment_method=row["payment_method"],
            payment_status=row["payment_status"],
            transaction_reference=row["transaction_reference"] if "transaction_reference" in keys else None,
            cashier_user_id=row["cashier_user_id"] if "cashier_user_id" in keys else None,
            cashier_name=row["cashier_name"] if "cashier_name" in keys else None,
            payment_time=row["payment_time"] if "payment_time" in keys else "",
        )

@dataclass
class AuditLog:
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    details: Optional[str]
    created_at: str

    @classmethod
    def from_row(cls, row) -> "AuditLog":
        keys = row.keys()
        return cls(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in keys else None,
            username=row["username"] if "username" in keys else None,
            action=row["action"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"] if "entity_id" in keys else None,
            details=row["details"] if "details" in keys else None,
            created_at=row["created_at"],
        )
