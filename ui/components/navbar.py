"""
ParkSmart Pro — Top Navigation Bar Component
"""

import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from config import THEME, APP_NAME, APP_VERSION

class TopNavBar(tk.Frame):
    def __init__(self, parent, on_logout, **kwargs):
        super().__init__(parent, bg=THEME["bg_header"], height=56, bd=1, relief="solid", **kwargs)
        self.config(highlightbackground=THEME["border"], highlightcolor=THEME["border"], highlightthickness=0)
        self.pack_propagate(False)

        self.on_logout = on_logout

        # Left: Active View Title
        self.left_frame = tk.Frame(self, bg=THEME["bg_header"], padx=20)
        self.left_frame.pack(side="left", fill="y")

        self.lbl_view_title = tk.Label(
            self.left_frame, text="Dashboard Overview",
            font=(THEME["font_family"], 13, "bold"),
            bg=THEME["bg_header"], fg=THEME["text_dark"]
        )
        self.lbl_view_title.pack(side="left", anchor="center")

        # Right container
        self.right_frame = tk.Frame(self, bg=THEME["bg_header"], padx=20)
        self.right_frame.pack(side="right", fill="y")

        # Live Clock
        self.lbl_clock = tk.Label(
            self.right_frame, text="",
            font=("Consolas", 10),
            bg=THEME["bg_header"], fg=THEME["text_muted"]
        )
        self.lbl_clock.pack(side="left", padx=(0, 20))

        # Alert Badge Indicator
        self.alert_badge = tk.Label(
            self.right_frame, text="",
            font=(THEME["font_family"], 8, "bold"),
            bg=THEME["bg_header"], fg=THEME["danger"]
        )
        self.alert_badge.pack(side="left", padx=(0, 15))

        # User Pill Badge
        self.user_pill = tk.Label(
            self.right_frame, text="👤 User",
            font=(THEME["font_family"], 9, "bold"),
            bg="#DBEAFE", fg="#1E40AF", padx=10, pady=4
        )
        self.user_pill.pack(side="left", padx=(0, 15))

        # Logout Button
        self.btn_logout = tk.Button(
            self.right_frame, text="🚪 Logout",
            font=(THEME["font_family"], 9),
            bg="#F1F5F9", fg=THEME["text_dark"],
            bd=1, relief="flat", padx=10, pady=3,
            command=self.on_logout, cursor="hand2"
        )
        self.btn_logout.pack(side="left")

        self._update_clock()

    def set_view_title(self, title: str):
        self.lbl_view_title.config(text=title)

    def set_user_info(self, full_name: str, role_name: str):
        self.user_pill.config(text=f"👤 {full_name} ({role_name.upper()})")

    def set_alert(self, alert_text: str = "", is_critical: bool = False):
        if alert_text:
            fg = THEME["danger"] if is_critical else THEME["warning"]
            self.alert_badge.config(text=f"⚠️ {alert_text}", fg=fg)
        else:
            self.alert_badge.config(text="")

    def _update_clock(self):
        now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.lbl_clock.config(text=now_str)
        self.after(1000, self._update_clock)
