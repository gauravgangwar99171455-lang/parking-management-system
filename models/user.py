"""
ParkSmart Pro — User and Role Domain Models
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Role:
    id: int
    name: str
    description: Optional[str] = None

@dataclass
class User:
    id: int
    username: str
    full_name: str
    role_id: int
    role_name: str
    is_active: bool = True
    last_login: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            full_name=row["full_name"],
            role_id=row["role_id"],
            role_name=row["role_name"] if "role_name" in row.keys() else "",
            is_active=bool(row["is_active"]),
            last_login=row["last_login"] if "last_login" in row.keys() else None,
            created_at=row["created_at"] if "created_at" in row.keys() else None,
        )

    def is_admin(self) -> bool:
        return self.role_name == "admin"

    def is_operator(self) -> bool:
        return self.role_name in ("admin", "operator")

    def is_auditor(self) -> bool:
        return True  # all authenticated users have read access
