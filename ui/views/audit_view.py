"""
ParkSmart Pro — Audit Trail & Traceability View
TQM Quality Attribute: Observability, Traceability & Non-Repudiation (ISO 9001)
"""

import tkinter as tk
from tkinter import ttk
from config import THEME
from services.audit_service import audit_service
from ui.components.paginated_table import PaginatedTable

class AuditView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.current_page = 1
        self.page_size = 25

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        self.content_frame.pack(fill="both", expand=True)

        self._build_filter_bar()
        self._build_table()

    def _build_filter_bar(self):
        bar = tk.Frame(self.content_frame, bg="#FFFFFF", padx=16, pady=12, bd=1, relief="solid")
        bar.config(highlightbackground=THEME["border"], highlightthickness=0)
        bar.pack(fill="x", pady=(0, 15))

        tk.Label(bar, text="🛡️ System Audit Trail", font=(THEME["font_family"], 12, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(side="left", padx=(0, 20))

        tk.Label(bar, text="Action Filter:", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(side="left", padx=(0, 4))
        self.cb_action = ttk.Combobox(
            bar,
            values=["ALL", "VEHICLE_ENTRY", "VEHICLE_EXIT", "ADD_SLOT", "UPDATE_SLOT_STATUS",
                    "CREATE_RESERVATION", "CANCEL_RESERVATION", "UPDATE_TARIFF", "BACKUP_DATABASE", "RESTORE_DATABASE"],
            state="readonly", width=18
        )
        self.cb_action.current(0)
        self.cb_action.pack(side="left", padx=(0, 15))
        self.cb_action.bind("<<ComboboxSelected>>", lambda e: self.refresh_logs(1))

        btn_refresh = ttk.Button(bar, text="Refresh Logs", style="Secondary.TButton", command=lambda: self.refresh_logs(1))
        btn_refresh.pack(side="left")

        tk.Label(
            bar, text="Immutable Event Log (Read-Only)",
            font=(THEME["font_family"], 8, "italic"), bg="#FFFFFF", fg=THEME["text_muted"]
        ).pack(side="right")

    def _build_table(self):
        cols = [
            {"id": "id", "text": "Log ID", "width": 60, "anchor": "center"},
            {"id": "timestamp", "text": "Timestamp", "width": 140, "anchor": "w"},
            {"id": "user", "text": "User", "width": 100, "anchor": "w"},
            {"id": "action", "text": "Action Type", "width": 140, "anchor": "w"},
            {"id": "entity_type", "text": "Entity", "width": 90, "anchor": "center"},
            {"id": "entity_id", "text": "Target ID", "width": 130, "anchor": "w"},
            {"id": "details", "text": "Operational Details & Payload", "width": 380, "anchor": "w"},
        ]

        self.table = PaginatedTable(
            self.content_frame,
            columns=cols,
            on_page_change=self._on_page_change
        )
        self.table.pack(fill="both", expand=True)

    def refresh_logs(self, page: int = 1):
        self.current_page = page
        action_val = self.cb_action.get()
        action_param = None if action_val == "ALL" else action_val
        offset = (self.current_page - 1) * self.page_size

        logs, total = audit_service.get_logs(
            limit=self.page_size,
            offset=offset,
            action=action_param
        )

        rows = []
        for l in logs:
            rows.append([
                l.id,
                l.created_at,
                l.username or "system",
                l.action,
                l.entity_type,
                l.entity_id or "-",
                l.details or "-"
            ])

        self.table.set_data(rows, total, self.current_page, self.page_size)

    def _on_page_change(self, page, size, sort_col, sort_desc):
        self.page_size = size
        self.refresh_logs(page)
