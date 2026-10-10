"""
ParkSmart Pro — Audit Trail Service
TQM Principle: Traceability & Process Standardization
"""

from typing import List, Optional, Tuple
from database.connection import get_db_connection
from models.payment import AuditLog
from utils.logger import get_logger

logger = get_logger("audit_service")

class AuditService:
    def log(self, action: str, entity_type: str, entity_id: Optional[str] = None,
            details: Optional[str] = None, user_id: Optional[int] = None,
            username: Optional[str] = None, conn=None) -> None:
        """
        Record an immutable event into audit_logs.
        Can run within an existing connection/transaction or create its own.
        """
        owns_conn = conn is None
        if owns_conn:
            conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO audit_logs (user_id, username, action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, action, entity_type, str(entity_id) if entity_id else None, details))
            if owns_conn:
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")
        finally:
            if owns_conn and conn:
                conn.close()

    def get_logs(self, limit: int = 50, offset: int = 0, action: Optional[str] = None,
                 entity_type: Optional[str] = None) -> Tuple[List[AuditLog], int]:
        """Retrieve paginated audit logs."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []

            if action:
                query += " AND action = ?"
                params.append(action)
            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            # Count total
            count_query = query.replace("SELECT *", "SELECT COUNT(*)")
            cur.execute(count_query, params)
            total = cur.fetchone()[0]

            query += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cur.execute(query, params)
            rows = cur.fetchall()

            logs = [AuditLog.from_row(r) for r in rows]
            return logs, total
        finally:
            conn.close()

audit_service = AuditService()
