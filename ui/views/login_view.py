"""
ParkSmart Pro — Login View Component
TQM Quality Attribute: Usability & Security (ISO/IEC 25010)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME, APP_NAME, APP_SUBTITLE, APP_VERSION
from services.auth_service import auth_service

class LoginView(tk.Frame):
    def __init__(self, parent, on_login_success, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_login_success = on_login_success

        # Center Container
        center_box = tk.Frame(self, bg=THEME["bg_main"])
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        # Login Card
        card = tk.Frame(center_box, bg="#FFFFFF", padx=35, pady=35, bd=1, relief="solid")
        card.config(highlightbackground=THEME["border"], highlightcolor=THEME["border"], highlightthickness=0)
        card.pack()

        # Branding
        lbl_icon = tk.Label(card, text="🅿️", font=(THEME["font_family"], 32), bg="#FFFFFF")
        lbl_icon.pack()

        lbl_app = tk.Label(
            card, text=APP_NAME,
            font=(THEME["font_family"], 16, "bold"),
            bg="#FFFFFF", fg=THEME["text_dark"]
        )
        lbl_app.pack(pady=(4, 2))

        lbl_sub = tk.Label(
            card, text=APP_SUBTITLE,
            font=(THEME["font_family"], 9),
            bg="#FFFFFF", fg=THEME["text_muted"]
        )
        lbl_sub.pack(pady=(0, 20))

        # Error / Status Banner
        self.lbl_msg = tk.Label(
            card, text="",
            font=(THEME["font_family"], 9, "bold"),
            bg="#FFFFFF", fg=THEME["danger"]
        )
        self.lbl_msg.pack(pady=(0, 10))

        # Username Input
        tk.Label(card, text="Username", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_user = ttk.Entry(card, width=32, font=(THEME["font_family"], 10))
        self.ent_user.pack(fill="x", pady=(4, 14))
        self.ent_user.focus_set()

        # Password Input
        tk.Label(card, text="Password", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_pass = ttk.Entry(card, width=32, font=(THEME["font_family"], 10), show="●")
        self.ent_pass.pack(fill="x", pady=(4, 20))
        self.ent_pass.bind("<Return>", lambda e: self._do_login())

        # Login Button
        self.btn_login = ttk.Button(
            card, text="Sign In to System",
            style="Primary.TButton",
            command=self._do_login,
            cursor="hand2"
        )
        self.btn_login.pack(fill="x", pady=(0, 20))

        # Divider
        tk.Frame(card, bg=THEME["border"], height=1).pack(fill="x", pady=(0, 15))

        # Demo Credentials Fast Fill
        tk.Label(
            card, text="Quick Demo Sign-In (Click to Autofill):",
            font=(THEME["font_family"], 8, "bold"),
            bg="#FFFFFF", fg=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 6))

        pills_frame = tk.Frame(card, bg="#FFFFFF")
        pills_frame.pack(fill="x")

        self._create_demo_pill(pills_frame, "Admin", "admin", "admin123", "#2563EB")
        self._create_demo_pill(pills_frame, "Operator", "operator", "operator123", "#10B981")
        self._create_demo_pill(pills_frame, "Auditor", "auditor", "auditor123", "#64748B")

        # Footer
        lbl_foot = tk.Label(
            card, text="TQM Quality Assurance Project • Local Secure Auth",
            font=(THEME["font_family"], 7),
            bg="#FFFFFF", fg=THEME["text_muted"]
        )
        lbl_foot.pack(pady=(20, 0))

    def _create_demo_pill(self, parent, role, u, p, color):
        btn = tk.Button(
            parent, text=f"{role}", font=(THEME["font_family"], 8),
            bg="#F1F5F9", fg=color, activebackground="#E2E8F0",
            bd=1, relief="flat", padx=6, pady=2, cursor="hand2",
            command=lambda: self._autofill(u, p)
        )
        btn.pack(side="left", padx=(0, 6))

    def _autofill(self, u: str, p: str):
        self.ent_user.delete(0, tk.END)
        self.ent_user.insert(0, u)
        self.ent_pass.delete(0, tk.END)
        self.ent_pass.insert(0, p)
        self.lbl_msg.config(text="")

    def _do_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get()

        ok, user, msg = auth_service.authenticate(username, password)
        if ok:
            self.lbl_msg.config(text="")
            self.on_login_success(user)
        else:
            self.lbl_msg.config(text=msg)
            self.ent_pass.delete(0, tk.END)
            self.ent_pass.focus_set()
