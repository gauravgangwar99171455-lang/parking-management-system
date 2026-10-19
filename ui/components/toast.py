"""
ParkSmart Pro — Toast Notification & Alert Banner Component
"""

import tkinter as tk
from config import THEME

class AlertBanner(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#FEF3C7", bd=1, relief="solid", **kwargs)
        self.config(highlightbackground="#F59E0B", highlightthickness=0)
        self.lbl_text = tk.Label(self, text="", bg="#FEF3C7", fg="#92400E",
                                 font=(THEME["font_family"], 9, "bold"), padx=12, pady=6)
        self.lbl_text.pack(side="left", fill="both", expand=True)

        self.btn_close = tk.Button(self, text="✕", bg="#FEF3C7", fg="#92400E",
                                   bd=0, relief="flat", font=(THEME["font_family"], 8, "bold"),
                                   command=self.hide, cursor="hand2")
        self.btn_close.pack(side="right", padx=8)
        self.pack_forget()

    def show(self, message: str, level: str = "warning"):
        colors = {
            "warning": {"bg": "#FEF3C7", "fg": "#92400E", "border": "#F59E0B"},
            "danger": {"bg": "#FEE2E2", "fg": "#991B1B", "border": "#EF4444"},
            "success": {"bg": "#DCFCE7", "fg": "#166534", "border": "#10B981"},
            "info": {"bg": "#DBEAFE", "fg": "#1E40AF", "border": "#3B82F6"},
        }
        theme = colors.get(level, colors["warning"])
        self.config(bg=theme["bg"])
        self.lbl_text.config(text=message, bg=theme["bg"], fg=theme["fg"])
        self.btn_close.config(bg=theme["bg"], fg=theme["fg"])
        self.pack(fill="x", padx=15, pady=(10, 0))

    def hide(self):
        self.pack_forget()
