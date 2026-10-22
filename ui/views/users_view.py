"""
ParkSmart Pro — User Management & RBAC View
TQM Quality Attribute: Security & Role-Based Access Control
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME
from services.auth_service import auth_service
from utils.validators import validate_username, validate_password_strength

class UsersView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=25, pady=20)
        self.content_frame.pack(fill="both", expand=True)

        self._build_header()
        self._build_split_view()

    def _build_header(self):
        bar = tk.Frame(self.content_frame, bg="#FFFFFF", padx=18, pady=14, bd=1, relief="solid")
        bar.config(highlightbackground=THEME["border"], highlightthickness=0)
        bar.pack(fill="x", pady=(0, 15))

        tk.Label(
            bar, text="👥 User Management & Role-Based Access Control",
            font=(THEME["font_family"], 13, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]
        ).pack(side="left")

        btn_toggle = ttk.Button(bar, text="Toggle Active Status", style="Secondary.TButton", command=self._toggle_user)
        btn_toggle.pack(side="right")

    def _build_split_view(self):
        split = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        split.pack(fill="both", expand=True)

        # Left: User List Table
        left = tk.Frame(split, bg="#FFFFFF", padx=15, pady=15, bd=1, relief="solid")
        left.config(highlightbackground=THEME["border"], highlightthickness=0)
        left.pack(side="left", fill="both", expand=True, padx=(0, 15))

        cols = ("id", "username", "full_name", "role", "active", "last_login")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", style="Custom.Treeview")
        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Username", anchor="w")
        self.tree.heading("full_name", text="Full Name", anchor="w")
        self.tree.heading("role", text="Role", anchor="center")
        self.tree.heading("active", text="Status", anchor="center")
        self.tree.heading("last_login", text="Last Login", anchor="w")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("username", width=120)
        self.tree.column("full_name", width=150)
        self.tree.column("role", width=90, anchor="center")
        self.tree.column("active", width=80, anchor="center")
        self.tree.column("last_login", width=140)

        self.tree.pack(fill="both", expand=True)

        # Right: Create User Form Card
        right = tk.Frame(split, bg="#FFFFFF", padx=20, pady=18, bd=1, relief="solid", width=290)
        right.config(highlightbackground=THEME["border"], highlightthickness=0)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="Create New User Account", font=(THEME["font_family"], 11, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 14))

        tk.Label(right, text="Username *", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_user = ttk.Entry(right)
        self.ent_user.pack(fill="x", pady=(2, 8))

        tk.Label(right, text="Full Name *", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_name = ttk.Entry(right)
        self.ent_name.pack(fill="x", pady=(2, 8))

        tk.Label(right, text="Password *", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_pwd = ttk.Entry(right, show="●")
        self.ent_pwd.pack(fill="x", pady=(2, 8))

        tk.Label(right, text="Assigned System Role *", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.cb_role = ttk.Combobox(right, values=["operator", "auditor", "admin"], state="readonly")
        self.cb_role.current(0)
        self.cb_role.pack(fill="x", pady=(2, 16))

        btn_create = ttk.Button(right, text="Create Account", style="Primary.TButton", command=self._create_user)
        btn_create.pack(fill="x")

    def refresh_users(self):
        users = auth_service.get_all_users()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for u in users:
            state_str = "ACTIVE" if u.is_active else "DISABLED"
            self.tree.insert("", "end", values=(
                u.id,
                u.username,
                u.full_name,
                u.role_name.upper(),
                state_str,
                u.last_login or "Never"
            ))

    def _create_user(self):
        u = self.ent_user.get().strip()
        name = self.ent_name.get().strip()
        p = self.ent_pwd.get()
        role = self.cb_role.get()

        ok_u, msg_u = validate_username(u)
        if not ok_u:
            messagebox.showerror("Validation Error", msg_u)
            return

        ok_p, msg_p = validate_password_strength(p)
        if not ok_p:
            messagebox.showerror("Validation Error", msg_p)
            return

        if not name:
            messagebox.showerror("Validation Error", "Full name is required.")
            return

        ok, msg = auth_service.create_user(u, p, name, role)
        if ok:
            messagebox.showinfo("Success", msg)
            self.ent_user.delete(0, tk.END)
            self.ent_name.delete(0, tk.END)
            self.ent_pwd.delete(0, tk.END)
            self.refresh_users()
        else:
            messagebox.showerror("Error", msg)

    def _toggle_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a user account to toggle active state.")
            return

        vals = self.tree.item(sel[0], "values")
        user_id = int(vals[0])
        uname = vals[1]

        if uname == "admin":
            messagebox.showerror("Protected Account", "Default super-admin account cannot be deactivated.")
            return

        ok, msg = auth_service.toggle_user_active(user_id)
        if ok:
            messagebox.showinfo("Updated", msg)
            self.refresh_users()
        else:
            messagebox.showerror("Error", msg)
