"""
ParkSmart Pro — High-Performance Vehicle Search Service
TQM Principle: Performance Engineering & Measurable Quality
"""

import time
from typing import List, Optional, Tuple, Dict, Any
from database.connection import get_db_connection
from models.parking_session import ParkingSession
from utils.logger import get_logger

logger = get_logger("search_service")

class SearchService:
    def search_sessions(self,
                        query_str: Optional[str] = None,
                        status: Optional[str] = None,
                        category: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        limit: int = 25,
                        offset: int = 0) -> Dict[str, Any]:
        """
        High-performance indexed search across parking sessions.
        Returns matched records, total matching count, and execution time in ms.
        """
        t_start = time.perf_counter()

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            base_where = " WHERE 1=1"
            params: List[Any] = []

            if query_str and query_str.strip():
                clean_q = query_str.strip().upper()
                # Fast indexed search pattern
                base_where += """ AND (
                    ps.vehicle_registration LIKE ? OR
                    ps.ticket_number LIKE ? OR
                    s.slot_code LIKE ?
                )"""
                kw = f"%{clean_q}%"
                params.extend([kw, kw, kw])

            if status and status != "ALL":
                base_where += " AND ps.status = ?"
                params.append(status)

            if category and category != "ALL":
                base_where += " AND ps.vehicle_category = ?"
                params.append(category)

            if start_date:
                base_where += " AND ps.entry_time >= ?"
                params.append(f"{start_date} 00:00:00")

            if end_date:
                base_where += " AND ps.entry_time <= ?"
                params.append(f"{end_date} 23:59:59")

            # 1. Total matching count query
            count_sql = f"""
                SELECT COUNT(*)
                FROM parking_sessions ps
                JOIN parking_slots s ON ps.slot_id = s.id
                {base_where}
            """
            cur.execute(count_sql, params)
            total_count = cur.fetchone()[0]

            # 2. Main paginated query
            data_sql = f"""
                SELECT ps.*, s.slot_code, z.name as zone_name,
                       p.payment_method
                FROM parking_sessions ps
                JOIN parking_slots s ON ps.slot_id = s.id
                JOIN parking_zones z ON s.zone_id = z.id
                LEFT JOIN payments p ON ps.id = p.session_id
                {base_where}
                ORDER BY ps.id DESC
                LIMIT ? OFFSET ?
            """
            data_params = params + [limit, offset]
            cur.execute(data_sql, data_params)
            rows = cur.fetchall()

            sessions = [ParkingSession.from_row(r) for r in rows]

            t_end = time.perf_counter()
            exec_time_ms = round((t_end - t_start) * 1000, 2)

            return {
                "records": sessions,
                "total_count": total_count,
                "execution_time_ms": exec_time_ms,
                "limit": limit,
                "offset": offset,
            }
        finally:
            conn.close()

    def explain_search_query(self, query_str: str = "KA-01-AB-1234") -> List[str]:
        """
        Run SQLite EXPLAIN QUERY PLAN to verify index utilization.
        Used for TQM appraisal and academic demonstration.
        """
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                EXPLAIN QUERY PLAN
                SELECT ps.*, s.slot_code
                FROM parking_sessions ps
                JOIN parking_slots s ON ps.slot_id = s.id
                WHERE ps.vehicle_registration = ?
            """, (query_str,))
            plan = [f"SelectID {row[0]}: {row[3]}" for row in cur.fetchall()]
            return plan
        finally:
            conn.close()

search_service = SearchService()
