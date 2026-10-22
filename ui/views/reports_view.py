"""
ParkSmart Pro — Analytical Reporting View
TQM Quality Attribute: Data-Driven Decision Making & Financial Integrity
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from pathlib import Path
from config import THEME, REPORTS_DIR
from services.report_service import report_service
from ui.components.charts import BarChart
from utils.formatters import format_currency
from utils.export_helpers import export_rows_to_csv

class ReportsView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        self.content_frame.pack(fill="both", expand=True)

        self._build_filter_bar()
        self._build_kpi_summary()
        self._build_details_split()

    def _build_filter_bar(self):
        bar = tk.Frame(self.content_frame, bg="#FFFFFF", padx=16, pady=12, bd=1, relief="solid")
        bar.config(highlightbackground=THEME["border"], highlightthickness=0)
        bar.pack(fill="x", pady=(0, 15))

        tk.Label(bar, text="📈 Analytical Reports", font=(THEME["font_family"], 12, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(side="left", padx=(0, 15))

        # Preset Range Dropdown
        tk.Label(bar, text="Period:", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(side="left", padx=(0, 4))
        self.cb_period = ttk.Combobox(bar, values=["Today", "Last 7 Days", "This Month", "All Time"], state="readonly", width=12)
        self.cb_period.current(1) # Default: Last 7 Days
        self.cb_period.pack(side="left", padx=(0, 12))
        self.cb_period.bind("<<ComboboxSelected>>", self._on_period_change)

        # Start Date
        tk.Label(bar, text="From:", font=(THEME["font_family"], 9), bg="#FFFFFF").pack(side="left", padx=(0, 2))
        self.ent_from = ttk.Entry(bar, width=11)
        self.ent_from.pack(side="left", padx=(0, 8))

        # End Date
        tk.Label(bar, text="To:", font=(THEME["font_family"], 9), bg="#FFFFFF").pack(side="left", padx=(0, 2))
        self.ent_to = ttk.Entry(bar, width=11)
        self.ent_to.pack(side="left", padx=(0, 12))

        # Category Filter
        tk.Label(bar, text="Category:", font=(THEME["font_family"], 9), bg="#FFFFFF").pack(side="left", padx=(0, 2))
        self.cb_cat = ttk.Combobox(bar, values=["ALL", "CAR", "TWO_WHEELER", "SUV", "COMMERCIAL", "EV"],
                                   state="readonly", width=10)
        self.cb_cat.current(0)
        self.cb_cat.pack(side="left", padx=(0, 15))

        btn_run = ttk.Button(bar, text="Generate Report", style="Primary.TButton", command=self.generate_report)
        btn_run.pack(side="left", padx=(0, 10))

        # Export CSV Button
        btn_csv = ttk.Button(bar, text="📥 Export CSV", style="Secondary.TButton", command=self._export_csv)
        btn_csv.pack(side="right")

    def _build_kpi_summary(self):
        kpi_row = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        kpi_row.pack(fill="x", pady=(0, 15))

        self.kpi_sessions = self._make_kpi_card(kpi_row, "Completed Sessions", "0", "#2563EB")
        self.kpi_gross = self._make_kpi_card(kpi_row, "Gross Billed Revenue", "$0.00", "#06B6D4")
        self.kpi_discounts = self._make_kpi_card(kpi_row, "Authorized Discounts", "$0.00", "#F59E0B")
        self.kpi_net = self._make_kpi_card(kpi_row, "Net Collected Revenue", "$0.00", "#10B981")

    def _make_kpi_card(self, parent, title: str, val: str, accent: str):
        card = tk.Frame(parent, bg="#FFFFFF", padx=15, pady=10, bd=1, relief="solid")
        card.config(highlightbackground=THEME["border"], highlightthickness=0)
        card.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Frame(card, bg=accent, height=3).pack(fill="x", side="top", pady=(0, 6))

        tk.Label(card, text=title.upper(), font=(THEME["font_family"], 8, "bold"),
                 bg="#FFFFFF", fg=THEME["text_muted"]).pack(anchor="w")

        lbl_val = tk.Label(card, text=val, font=(THEME["font_family"], 16, "bold"),
                           bg="#FFFFFF", fg=THEME["text_dark"])
        lbl_val.pack(anchor="w", pady=(2, 0))
        return lbl_val

    def _build_details_split(self):
        split = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        split.pack(fill="both", expand=True)

        # Left Column: Category & Payment Tables
        left = tk.Frame(split, bg=THEME["bg_main"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Category Breakdown Table Card
        c_card = tk.Frame(left, bg="#FFFFFF", padx=12, pady=10, bd=1, relief="solid")
        c_card.config(highlightbackground=THEME["border"], highlightthickness=0)
        c_card.pack(fill="both", expand=True, pady=(0, 10))

        tk.Label(c_card, text="Revenue by Vehicle Category", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 6))

        c_cols = ("cat", "count", "gross", "discount", "net")
        self.tree_cat = ttk.Treeview(c_card, columns=c_cols, show="headings", height=4, style="Custom.Treeview")
        self.tree_cat.heading("cat", text="Category", anchor="w")
        self.tree_cat.heading("count", text="Sessions", anchor="center")
        self.tree_cat.heading("gross", text="Gross", anchor="e")
        self.tree_cat.heading("discount", text="Discounts", anchor="e")
        self.tree_cat.heading("net", text="Net Revenue", anchor="e")

        self.tree_cat.column("cat", width=120)
        self.tree_cat.column("count", width=70, anchor="center")
        self.tree_cat.column("gross", width=85, anchor="e")
        self.tree_cat.column("discount", width=85, anchor="e")
        self.tree_cat.column("net", width=95, anchor="e")

        self.tree_cat.pack(fill="both", expand=True)

        # Payment Mode Table Card
        p_card = tk.Frame(left, bg="#FFFFFF", padx=12, pady=10, bd=1, relief="solid")
        p_card.config(highlightbackground=THEME["border"], highlightthickness=0)
        p_card.pack(fill="both", expand=True)

        tk.Label(p_card, text="Revenue by Payment Mode", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 6))

        p_cols = ("mode", "tx_count", "total")
        self.tree_pay = ttk.Treeview(p_card, columns=p_cols, show="headings", height=4, style="Custom.Treeview")
        self.tree_pay.heading("mode", text="Payment Mode", anchor="w")
        self.tree_pay.heading("tx_count", text="Transactions", anchor="center")
        self.tree_pay.heading("total", text="Total Collected", anchor="e")

        self.tree_pay.column("mode", width=140)
        self.tree_pay.column("tx_count", width=100, anchor="center")
        self.tree_pay.column("total", width=120, anchor="e")

        self.tree_pay.pack(fill="both", expand=True)

        # Right Column: Parking Duration Distribution Chart Card
        right = tk.Frame(split, bg="#FFFFFF", padx=15, pady=15, bd=1, relief="solid")
        right.config(highlightbackground=THEME["border"], highlightthickness=0)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="Parking Duration Distribution", font=(THEME["font_family"], 10, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 4))

        tk.Label(right, text="Number of parked sessions grouped by stay time", font=(THEME["font_family"], 8),
                 bg="#FFFFFF", fg=THEME["text_muted"]).pack(anchor="w", pady=(0, 8))

        self.chart_dur = BarChart(right, width=320, height=230)
        self.chart_dur.pack(fill="both", expand=True)

    def _on_period_change(self, event=None):
        period = self.cb_period.get()
        now = datetime.now()
        if period == "Today":
            s = now.strftime("%Y-%m-%d")
            e = s
        elif period == "Last 7 Days":
            s = (now - timedelta(days=6)).strftime("%Y-%m-%d")
            e = now.strftime("%Y-%m-%d")
        elif period == "This Month":
            s = now.strftime("%Y-%m-01")
            e = now.strftime("%Y-%m-%d")
        else: # All Time
            s = "2020-01-01"
            e = now.strftime("%Y-%m-%d")

        self.ent_from.delete(0, tk.END)
        self.ent_from.insert(0, s)
        self.ent_to.delete(0, tk.END)
        self.ent_to.insert(0, e)

    def generate_report(self):
        s_date = self.ent_from.get().strip() or "2020-01-01"
        e_date = self.ent_to.get().strip() or datetime.now().strftime("%Y-%m-%d")
        cat = self.cb_cat.get()

        res = report_service.get_financial_report(s_date, e_date, category=cat)
        summ = res["summary"]

        self.kpi_sessions.config(text=f"{summ['total_completed_sessions']:,}")
        self.kpi_gross.config(text=format_currency(summ["total_gross_cents"]))
        self.kpi_discounts.config(text=format_currency(summ["total_discount_cents"]))
        self.kpi_net.config(text=format_currency(summ["total_net_cents"]))

        # Category Table
        for item in self.tree_cat.get_children():
            self.tree_cat.delete(item)
        for r in res["by_category"]:
            self.tree_cat.insert("", "end", values=(
                r["vehicle_category"],
                f"{r['session_count']:,}",
                format_currency(r["gross_cents"]),
                format_currency(r["discount_cents"]),
                format_currency(r["net_cents"])
            ))

        # Payment Table
        for item in self.tree_pay.get_children():
            self.tree_pay.delete(item)
        for r in res["by_payment"]:
            self.tree_pay.insert("", "end", values=(
                r["payment_method"],
                f"{r['tx_count']:,}",
                format_currency(r["total_cents"])
            ))

        # Duration Distribution
        dur_data = report_service.get_duration_distribution(s_date, e_date)
        self.chart_dur.draw(
            categories=list(dur_data.keys()),
            values=[float(v) for v in dur_data.values()],
            color=THEME["primary"]
        )

        self.last_report = res

    def _export_csv(self):
        if not hasattr(self, "last_report") or not self.last_report:
            self.generate_report()

        filename = f"parksmart_financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        dest_path = filedialog.asksaveasfilename(
            initialdir=str(REPORTS_DIR),
            initialfile=filename,
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not dest_path:
            return

        headers = ["Category", "Session Count", "Gross Revenue (Cents)", "Discounts (Cents)", "Net Revenue (Cents)"]
        rows = []
        for r in self.last_report["by_category"]:
            rows.append([
                r["vehicle_category"], r["session_count"],
                r["gross_cents"], r["discount_cents"], r["net_cents"]
            ])

        ok, msg = export_rows_to_csv(Path(dest_path), headers, rows)
        if ok:
            messagebox.showinfo("Export Success", msg)
        else:
            messagebox.showerror("Export Failed", msg)
