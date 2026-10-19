"""
ParkSmart Pro — Modern Sidebar Navigation Component
TQM Quality Attribute: Usability & Role-Based Navigation
"""

import tkinter as tk
from config import THEME, APP_NAME, APP_VERSION

NAV_ITEMS = [
    {"key": "dashboard", "label": "📊  Dashboard", "roles": ["admin", "operator", "auditor"]},
    {"key": "slots", "label": "🅿️  Parking Slots", "roles": ["admin", "operator", "auditor"]},
    {"key": "entry", "label": "📥  Vehicle Entry", "roles": ["admin", "operator"]},
    {"key": "exit", "label": "📤  Vehicle Exit & Pay", "roles": ["admin", "operator"]},
    {"key": "search", "label": "🔍  Fast Search", "roles": ["admin", "operator", "auditor"]},
    {"key": "reservations", "label": "📅  Reservations", "roles": ["admin", "operator"]},
    {"key": "tariffs", "label": "💲  Tariffs & Rates", "roles": ["admin"]},
    {"key": "reports", "label": "📈  Analytical Reports", "roles": ["admin", "operator", "auditor"]},
    {"key": "imports", "label": "📂  CSV Import & Export", "roles": ["admin"]},
    {"key": "users", "label": "👥  User Management", "roles": ["admin"]},
    {"key": "audit", "label": "🛡️  Audit Trail", "roles": ["admin", "auditor"]},
    {"key": "backup", "label": "💾  Backup & Recovery", "roles": ["admin"]},
]

class Sidebar(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_sidebar"], width=230, **kwargs)
        self.pack_propagate(False)

        self.on_navigate = on_navigate
        self.nav_buttons = {}
        self.active_key = "dashboard"

        # Brand Header
        header = tk.Frame(self, bg=THEME["bg_sidebar"], padx=18, pady=18)
        header.pack(fill="x")

        lbl_app = tk.Label(
            header, text="🅿️ ParkSmart Pro",
            font=(THEME["font_family"], 13, "bold"),
            bg=THEME["bg_sidebar"], fg=THEME["text_light"]
        )
        lbl_app.pack(anchor="w")

        lbl_sub = tk.Label(
            header, text="Smart Parking Management System",
            font=(THEME["font_family"], 7),
            bg=THEME["bg_sidebar"], fg=THEME["text_muted"]
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Thin divider
        tk.Frame(self, bg="#1E293B", height=1).pack(fill="x", padx=14, pady=(0, 10))

        # Navigation Menu List Container
        self.menu_frame = tk.Frame(self, bg=THEME["bg_sidebar"])
        self.menu_frame.pack(fill="both", expand=True, padx=8)

        # Bottom Quality Footer
        footer = tk.Frame(self, bg=THEME["bg_sidebar"], padx=14, pady=14)
        footer.pack(fill="x", side="bottom")

        tk.Frame(self, bg="#1E293B", height=1).pack(fill="x", side="bottom", padx=14)

        lbl_tqm = tk.Label(
            footer, text="TQM Quality System",
            font=(THEME["font_family"], 8, "bold"),
            bg=THEME["bg_sidebar"], fg=THEME["text_muted"]
        )
        lbl_tqm.pack(anchor="w")

        lbl_iso = tk.Label(
            footer, text="ISO 9001 & ISO/IEC 25010\nWindows Native Desktop",
            font=(THEME["font_family"], 7),
            bg=THEME["bg_sidebar"], fg="#475569", justify="left"
        )
        lbl_iso.pack(anchor="w", pady=(2, 0))

    def update_role(self, role_name: str):
        """Re-render navigation buttons visible to the current role."""
        for w in self.menu_frame.winfo_children():
            w.destroy()
        self.nav_buttons.clear()

        for item in NAV_ITEMS:
            if role_name in item["roles"]:
                key = item["key"]
                label = item["label"]
                btn = tk.Button(
                    self.menu_frame,
                    text=label,
                    font=(THEME["font_family"], 9),
                    bg=THEME["bg_sidebar"],
                    fg="#94A3B8",
                    activebackground=THEME["bg_sidebar_hover"],
                    activeforeground=THEME["text_light"],
                    bd=0, relief="flat",
                    anchor="w",
                    padx=14, pady=7,
                    cursor="hand2",
                    command=lambda k=key: self._on_btn_click(k)
                )
                btn.pack(fill="x", pady=1)
                self.nav_buttons[key] = btn

        self.set_active(self.active_key)

    def set_active(self, key: str):
        self.active_key = key
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.config(bg=THEME["bg_sidebar_active"], fg="#FFFFFF", font=(THEME["font_family"], 9, "bold"))
            else:
                btn.config(bg=THEME["bg_sidebar"], fg="#94A3B8", font=(THEME["font_family"], 9))

    def _on_btn_click(self, key: str):
        self.set_active(key)
        self.on_navigate(key)
