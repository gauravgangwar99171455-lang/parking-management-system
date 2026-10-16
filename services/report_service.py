"""
ParkSmart Pro — Analytical Reporting & Dashboard Service
TQM Principle: Data-Driven Decision Making & SQL Aggregation Optimization
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database.connection import get_db_connection
from utils.logger import get_logger

logger = get_logger("report_service")

class ReportService:
    def get_dashboard_kpis(self) -> Dict[str, Any]:
        """
        Compute live KPI metrics calculated directly via optimized SQL queries.
        Never relies on duplicate maintained counters.
        """
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            today_date = datetime.now().strftime("%Y-%m-%d")
            first_day_month = datetime.now().strftime("%Y-%m-01")

            # 1. Slot Status Breakdown
            cur.execute("""
                SELECT
                    COUNT(*) as total_slots,
                    SUM(CASE WHEN status = 'AVAILABLE' AND is_active = 1 THEN 1 ELSE 0 END) as available_slots,
                    SUM(CASE WHEN status = 'OCCUPIED' AND is_active = 1 THEN 1 ELSE 0 END) as occupied_slots,
                    SUM(CASE WHEN status = 'RESERVED' AND is_active = 1 THEN 1 ELSE 0 END) as reserved_slots,
                    SUM(CASE WHEN status = 'MAINTENANCE' OR is_active = 0 THEN 1 ELSE 0 END) as maintenance_slots
                FROM parking_slots
            """)
            slot_stats = dict(cur.fetchone())

            total_slots = slot_stats["total_slots"] or 0
            occupied = slot_stats["occupied_slots"] or 0
            occupancy_pct = round((occupied / total_slots * 100), 1) if total_slots > 0 else 0.0

            # 2. Today's Inflow / Outflow
            cur.execute("""
                SELECT
                    SUM(CASE WHEN entry_time >= ? THEN 1 ELSE 0 END) as entered_today,
                    SUM(CASE WHEN exit_time >= ? AND status = 'COMPLETED' THEN 1 ELSE 0 END) as exited_today,
                    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as currently_parked
                FROM parking_sessions
            """, (f"{today_date} 00:00:00", f"{today_date} 00:00:00"))
            flow_stats = dict(cur.fetchone())

            # 3. Financial Metrics (Net collected revenue)
            cur.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN p.payment_time >= ? THEN p.amount_cents ELSE 0 END), 0) as today_revenue_cents,
                    COALESCE(SUM(CASE WHEN p.payment_time >= ? THEN p.amount_cents ELSE 0 END), 0) as month_revenue_cents
                FROM payments p
                WHERE p.payment_status = 'PAID'
            """, (f"{today_date} 00:00:00", f"{first_day_month} 00:00:00"))
            rev_stats = dict(cur.fetchone())

            # 4. Average Parking Duration (in minutes) for completed sessions today
            cur.execute("""
                SELECT COALESCE(AVG(duration_minutes), 0) as avg_duration_mins
                FROM parking_sessions
                WHERE exit_time >= ? AND status = 'COMPLETED'
            """, (f"{today_date} 00:00:00",))
            avg_duration = round(cur.fetchone()[0])

            # 5. Peak Parking Hour (hour with highest entry count in last 30 days)
            cur.execute("""
                SELECT strftime('%H', entry_time) as entry_hour, COUNT(*) as count
                FROM parking_sessions
                WHERE entry_time >= date('now', '-30 days')
                GROUP BY entry_hour
                ORDER BY count DESC LIMIT 1
            """)
            peak_row = cur.fetchone()
            peak_hour_str = f"{peak_row['entry_hour']}:00 - {int(peak_row['entry_hour'])+1:02d}:00" if peak_row else "12:00 - 13:00"

            # 6. Recent Entries and Exits (latest 8 sessions)
            cur.execute("""
                SELECT ps.id, ps.ticket_number, ps.vehicle_registration, ps.vehicle_category,
                       s.slot_code, ps.entry_time, ps.exit_time, ps.status, ps.net_amount_cents
                FROM parking_sessions ps
                JOIN parking_slots s ON ps.slot_id = s.id
                ORDER BY ps.id DESC LIMIT 8
            """)
            recent_sessions = [dict(r) for r in cur.fetchall()]

            # 7. Distribution by Vehicle Category
            cur.execute("""
                SELECT vehicle_category, COUNT(*) as count
                FROM parking_sessions
                WHERE status = 'ACTIVE'
                GROUP BY vehicle_category
            """)
            category_counts = {r["vehicle_category"]: r["count"] for r in cur.fetchall()}

            # 8. Past 7-Day Revenue Trends
            cur.execute("""
                SELECT strftime('%Y-%m-%d', payment_time) as p_date,
                       SUM(amount_cents) as daily_total_cents
                FROM payments
                WHERE payment_time >= date('now', '-6 days') AND payment_status = 'PAID'
                GROUP BY p_date
                ORDER BY p_date ASC
            """)
            daily_revenue = {r["p_date"]: r["daily_total_cents"] for r in cur.fetchall()}

            return {
                "total_slots": total_slots,
                "available_slots": slot_stats["available_slots"] or 0,
                "occupied_slots": occupied,
                "reserved_slots": slot_stats["reserved_slots"] or 0,
                "maintenance_slots": slot_stats["maintenance_slots"] or 0,
                "occupancy_percentage": occupancy_pct,
                "entered_today": flow_stats["entered_today"] or 0,
                "exited_today": flow_stats["exited_today"] or 0,
                "currently_parked": flow_stats["currently_parked"] or 0,
                "today_revenue_cents": rev_stats["today_revenue_cents"],
                "month_revenue_cents": rev_stats["month_revenue_cents"],
                "avg_duration_minutes": avg_duration,
                "peak_parking_hour": peak_hour_str,
                "recent_sessions": recent_sessions,
                "category_counts": category_counts,
                "daily_revenue": daily_revenue,
            }
        finally:
            conn.close()

    def get_financial_report(self, start_date: str, end_date: str,
                             category: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive financial summary with revenue by category and payment method.
        """
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            params = [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]
            cat_clause = ""
            if category and category != "ALL":
                cat_clause = " AND ps.vehicle_category = ?"
                params.append(category)

            # Overall Totals: Gross, Discounts, Net
            cur.execute(f"""
                SELECT
                    COUNT(ps.id) as total_completed_sessions,
                    COALESCE(SUM(ps.gross_amount_cents), 0) as total_gross_cents,
                    COALESCE(SUM(ps.discount_cents), 0) as total_discount_cents,
                    COALESCE(SUM(ps.net_amount_cents), 0) as total_net_cents
                FROM parking_sessions ps
                WHERE ps.exit_time BETWEEN ? AND ?
                  AND ps.status = 'COMPLETED'
                  {cat_clause}
            """, params)
            summary = dict(cur.fetchone())

            # Category Breakdown
            cur.execute(f"""
                SELECT
                    ps.vehicle_category,
                    COUNT(ps.id) as session_count,
                    COALESCE(SUM(ps.gross_amount_cents), 0) as gross_cents,
                    COALESCE(SUM(ps.discount_cents), 0) as discount_cents,
                    COALESCE(SUM(ps.net_amount_cents), 0) as net_cents
                FROM parking_sessions ps
                WHERE ps.exit_time BETWEEN ? AND ?
                  AND ps.status = 'COMPLETED'
                  {cat_clause}
                GROUP BY ps.vehicle_category
                ORDER BY net_cents DESC
            """, params)
            by_category = [dict(r) for r in cur.fetchall()]

            # Payment Method Breakdown
            cur.execute(f"""
                SELECT
                    p.payment_method,
                    COUNT(p.id) as tx_count,
                    COALESCE(SUM(p.amount_cents), 0) as total_cents
                FROM payments p
                JOIN parking_sessions ps ON p.session_id = ps.id
                WHERE p.payment_time BETWEEN ? AND ?
                  AND p.payment_status = 'PAID'
                  {cat_clause}
                GROUP BY p.payment_method
                ORDER BY total_cents DESC
            """, params)
            by_payment = [dict(r) for r in cur.fetchall()]

            return {
                "summary": summary,
                "by_category": by_category,
                "by_payment": by_payment,
            }
        finally:
            conn.close()

    def get_duration_distribution(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Group completed sessions into duration buckets: <1h, 1-2h, 2-4h, 4-8h, >8h.
        """
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    SUM(CASE WHEN duration_minutes <= 60 THEN 1 ELSE 0 END) as under_1h,
                    SUM(CASE WHEN duration_minutes > 60 AND duration_minutes <= 120 THEN 1 ELSE 0 END) as h1_to_2,
                    SUM(CASE WHEN duration_minutes > 120 AND duration_minutes <= 240 THEN 1 ELSE 0 END) as h2_to_4,
                    SUM(CASE WHEN duration_minutes > 240 AND duration_minutes <= 480 THEN 1 ELSE 0 END) as h4_to_8,
                    SUM(CASE WHEN duration_minutes > 480 THEN 1 ELSE 0 END) as over_8h
                FROM parking_sessions
                WHERE exit_time BETWEEN ? AND ?
                  AND status = 'COMPLETED'
            """, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
            row = cur.fetchone()
            return {
                "< 1 Hour": row["under_1h"] or 0,
                "1 - 2 Hours": row["h1_to_2"] or 0,
                "2 - 4 Hours": row["h2_to_4"] or 0,
                "4 - 8 Hours": row["h4_to_8"] or 0,
                "> 8 Hours": row["over_8h"] or 0,
            }
        finally:
            conn.close()

    def get_hourly_inflow_today(self) -> Dict[int, int]:
        """Return vehicle inflow count for every hour of the current day (0 to 23)."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            cur.execute("""
                SELECT CAST(strftime('%H', entry_time) AS INTEGER) as hr, COUNT(*) as count
                FROM parking_sessions
                WHERE entry_time >= ?
                GROUP BY hr
            """, (f"{today} 00:00:00",))
            data = {i: 0 for i in range(24)}
            for r in cur.fetchall():
                data[r["hr"]] = r["count"]
            return data
        finally:
            conn.close()

report_service = ReportService()
