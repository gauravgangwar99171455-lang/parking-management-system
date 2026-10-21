"""
ParkSmart Pro — Dashboard & Analytics View
TQM Quality Attribute: Usability & Real-Time Operational Awareness
"""

import tkinter as tk
from tkinter import ttk
from config import THEME
from services.report_service import report_service
from ui.components.cards import KPICard
from ui.components.charts import DonutChart, BarChart, LineTrendChart
from utils.formatters import format_currency

class DashboardView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        # Main Scrollable / Packing Container
        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        self.content_frame.pack(fill="both", expand=True)

        # Header Row: Section Label + Refresh Button
        header_row = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        header_row.pack(fill="x", pady=(0, 15))

        lbl_head = tk.Label(
            header_row, text="Operational Dashboard",
            font=(THEME["font_family"], 14, "bold"),
            bg=THEME["bg_main"], fg=THEME["text_dark"]
        )
        lbl_head.pack(side="left")

        btn_refresh = ttk.Button(
            header_row, text="🔄 Refresh Figures",
            style="Secondary.TButton",
            command=self.refresh_data, cursor="hand2"
        )
        btn_refresh.pack(side="right")

        # --------------------------------------------------------------------
        # 1. KPI Cards Row (4 cards top row)
        # --------------------------------------------------------------------
        self.kpi_frame_top = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        self.kpi_frame_top.pack(fill="x", pady=(0, 10))

        self.card_total = KPICard(self.kpi_frame_top, "Total Spaces", "0", "Capacity", "#2563EB", "🅿️")
        self.card_total.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.card_avail = KPICard(self.kpi_frame_top, "Available", "0", "Ready to park", "#10B981", "🟢")
        self.card_avail.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.card_occ = KPICard(self.kpi_frame_top, "Occupied", "0", "Vehicles parked", "#EF4444", "🚗")
        self.card_occ.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.card_rate = KPICard(self.kpi_frame_top, "Occupancy", "0.0%", "Target < 85%", "#F59E0B", "📊")
        self.card_rate.pack(side="left", fill="x", expand=True)

        # --------------------------------------------------------------------
        # 2. KPI Cards Row 2 (Financials & Flow)
        # --------------------------------------------------------------------
        self.kpi_frame_bottom = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        self.kpi_frame_bottom.pack(fill="x", pady=(0, 15))

        self.card_flow = KPICard(self.kpi_frame_bottom, "Today's Flow", "0 in / 0 out", "Daily Inflow", "#06B6D4", "🔄")
        self.card_flow.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.card_today_rev = KPICard(self.kpi_frame_bottom, "Today's Revenue", "$0.00", "Net Collected", "#10B981", "💵")
        self.card_today_rev.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.card_month_rev = KPICard(self.kpi_frame_bottom, "Monthly Revenue", "$0.00", "Current Month", "#2563EB", "💰")
        self.card_month_rev.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.card_peak = KPICard(self.kpi_frame_bottom, "Peak Hour", "-", "Avg Dur: 0m", "#8B5CF6", "⏱️")
        self.card_peak.pack(side="left", fill="x", expand=True)

        # --------------------------------------------------------------------
        # 3. Charts Row: Donut Chart + Category Bar Chart + Revenue Trend
        # --------------------------------------------------------------------
        charts_row = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        charts_row.pack(fill="both", expand=True, pady=(0, 15))

        # Chart Card 1: Occupancy Donut
        c1_card = tk.Frame(charts_row, bg="#FFFFFF", bd=1, relief="solid")
        c1_card.config(highlightbackground=THEME["border"], highlightthickness=0)
        c1_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(c1_card, text="Occupancy Breakdown", font=(THEME["font_family"], 10, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", padx=12, pady=(10, 4))
        self.donut_chart = DonutChart(c1_card, width=280, height=210)
        self.donut_chart.pack(fill="both", expand=True, padx=10, pady=5)

        # Chart Card 2: Vehicles by Category
        c2_card = tk.Frame(charts_row, bg="#FFFFFF", bd=1, relief="solid")
        c2_card.config(highlightbackground=THEME["border"], highlightthickness=0)
        c2_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(c2_card, text="Active Vehicles by Category", font=(THEME["font_family"], 10, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", padx=12, pady=(10, 4))
        self.cat_chart = BarChart(c2_card, width=280, height=210)
        self.cat_chart.pack(fill="both", expand=True, padx=10, pady=5)

        # Chart Card 3: 7-Day Revenue Trend
        c3_card = tk.Frame(charts_row, bg="#FFFFFF", bd=1, relief="solid")
        c3_card.config(highlightbackground=THEME["border"], highlightthickness=0)
        c3_card.pack(side="left", fill="both", expand=True)

        tk.Label(c3_card, text="7-Day Revenue Trend", font=(THEME["font_family"], 10, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", padx=12, pady=(10, 4))
        self.rev_chart = LineTrendChart(c3_card, width=280, height=210)
        self.rev_chart.pack(fill="both", expand=True, padx=10, pady=5)

        # --------------------------------------------------------------------
        # 4. Recent Activity Mini-Table
        # --------------------------------------------------------------------
        table_card = tk.Frame(self.content_frame, bg="#FFFFFF", bd=1, relief="solid")
        table_card.config(highlightbackground=THEME["border"], highlightthickness=0)
        table_card.pack(fill="both", expand=True)

        t_head = tk.Frame(table_card, bg="#FFFFFF", padx=12, pady=8)
        t_head.pack(fill="x")
        tk.Label(t_head, text="Recent Vehicle Parking Activity", font=(THEME["font_family"], 10, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(side="left")

        btn_all = tk.Button(
            t_head, text="View All Sessions →", font=(THEME["font_family"], 8, "bold"),
            bg="#FFFFFF", fg=THEME["primary"], bd=0, cursor="hand2",
            command=lambda: self.on_navigate("search")
        )
        btn_all.pack(side="right")

        cols = ("ticket", "reg", "cat", "slot", "entry", "status", "net")
        self.tree_recent = ttk.Treeview(table_card, columns=cols, show="headings", height=5, style="Custom.Treeview")
        self.tree_recent.heading("ticket", text="Ticket #", anchor="w")
        self.tree_recent.heading("reg", text="Vehicle Reg", anchor="w")
        self.tree_recent.heading("cat", text="Category", anchor="w")
        self.tree_recent.heading("slot", text="Slot", anchor="center")
        self.tree_recent.heading("entry", text="Entry Time", anchor="w")
        self.tree_recent.heading("status", text="Status", anchor="center")
        self.tree_recent.heading("net", text="Net Amount", anchor="e")

        self.tree_recent.column("ticket", width=140)
        self.tree_recent.column("reg", width=120)
        self.tree_recent.column("cat", width=100)
        self.tree_recent.column("slot", width=80, anchor="center")
        self.tree_recent.column("entry", width=150)
        self.tree_recent.column("status", width=90, anchor="center")
        self.tree_recent.column("net", width=90, anchor="e")

        self.tree_recent.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def refresh_data(self):
        """Fetch fresh KPI metrics and update UI elements."""
        kpis = report_service.get_dashboard_kpis()

        # Update KPI Cards
        tot = kpis["total_slots"]
        avail = kpis["available_slots"]
        occ = kpis["occupied_slots"]
        res = kpis["reserved_slots"]
        maint = kpis["maintenance_slots"]
        rate = kpis["occupancy_percentage"]

        self.card_total.update_value(str(tot), "Configured Slots")
        self.card_avail.update_value(str(avail), f"{round(avail/max(1,tot)*100)}% available")
        self.card_occ.update_value(str(occ), f"{kpis['currently_parked']} active parked")
        self.card_rate.update_value(f"{rate}%", "Near Capacity" if rate >= 85 else "Optimal Flow")

        self.card_flow.update_value(f"{kpis['entered_today']} In / {kpis['exited_today']} Out", "Today's movements")
        self.card_today_rev.update_value(format_currency(kpis["today_revenue_cents"]), "Collected Today")
        self.card_month_rev.update_value(format_currency(kpis["month_revenue_cents"]), "Collected This Month")
        self.card_peak.update_value(kpis["peak_parking_hour"], f"Avg Dur: {kpis['avg_duration_minutes']}m")

        # Update Donut Chart
        slices = [
            ("Available", avail, THEME["success"]),
            ("Occupied", occ, THEME["danger"]),
            ("Reserved", res, THEME["warning"]),
            ("Maintenance", maint, THEME["neutral"]),
        ]
        self.donut_chart.draw(slices, center_text=f"{rate}%", center_sub="Occupancy")

        # Update Category Bar Chart
        cat_counts = kpis["category_counts"]
        if cat_counts:
            cats = list(cat_counts.keys())
            vals = [float(v) for v in cat_counts.values()]
            self.cat_chart.draw(cats, vals, color=THEME["primary"])
        else:
            self.cat_chart.draw(["None"], [0.0])

        # Update Revenue Trend Line Chart
        daily_rev = kpis["daily_revenue"]
        if daily_rev:
            dates = list(daily_rev.keys())
            amounts = [v / 100.0 for v in daily_rev.values()]
            self.rev_chart.draw(dates, amounts, color=THEME["success"])
        else:
            self.rev_chart.draw(["Today"], [0.0])

        # Update Recent Activity Table
        for item in self.tree_recent.get_children():
            self.tree_recent.delete(item)

        for s in kpis["recent_sessions"]:
            amt_str = format_currency(s["net_amount_cents"]) if s["status"] == "COMPLETED" else "Active"
            self.tree_recent.insert("", "end", values=(
                s["ticket_number"],
                s["vehicle_registration"],
                s["vehicle_category"],
                s["slot_code"],
                s["entry_time"],
                s["status"],
                amt_str
            ))
