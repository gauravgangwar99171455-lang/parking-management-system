"""
ParkSmart Pro — Reusable KPI Summary Card Component
"""

import tkinter as tk
from tkinter import ttk
from config import THEME

class KPICard(tk.Frame):
    def __init__(self, parent, title: str, value: str, subtext: str = "",
                 accent_color: str = "#2563EB", icon: str = "📊", **kwargs):
        super().__init__(parent, bg=THEME["bg_card"], bd=1, relief="solid",
                         highlightthickness=0, **kwargs)
        self.config(highlightbackground=THEME["border"], highlightcolor=THEME["border"])

        # Left Accent Stripe
        self.stripe = tk.Frame(self, bg=accent_color, width=4)
        self.stripe.pack(side="left", fill="y")

        # Content Container
        self.content = tk.Frame(self, bg=THEME["bg_card"], padx=14, pady=10)
        self.content.pack(side="left", fill="both", expand=True)

        # Header Row: Title & Icon
        header_row = tk.Frame(self.content, bg=THEME["bg_card"])
        header_row.pack(fill="x")

        self.lbl_title = tk.Label(
            header_row, text=title.upper(), bg=THEME["bg_card"],
            fg=THEME["text_muted"], font=(THEME["font_family"], 8, "bold")
        )
        self.lbl_title.pack(side="left")

        self.lbl_icon = tk.Label(
            header_row, text=icon, bg=THEME["bg_card"],
            fg=accent_color, font=(THEME["font_family"], 12)
        )
        self.lbl_icon.pack(side="right")

        # Value
        self.lbl_val = tk.Label(
            self.content, text=value, bg=THEME["bg_card"],
            fg=THEME["text_dark"], font=(THEME["font_family"], 18, "bold"),
            anchor="w"
        )
        self.lbl_val.pack(fill="x", pady=(2, 0))

        # Subtext / Trend
        self.lbl_sub = tk.Label(
            self.content, text=subtext, bg=THEME["bg_card"],
            fg=THEME["text_muted"], font=(THEME["font_family"], 8),
            anchor="w"
        )
        self.lbl_sub.pack(fill="x")

    def update_value(self, new_val: str, new_sub: str = ""):
        self.lbl_val.config(text=new_val)
        if new_sub:
            self.lbl_sub.config(text=new_sub)
