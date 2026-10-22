"""
ParkSmart Pro — Database Backup & Disaster Recovery View
TQM Quality Attribute: Risk Management & Business Continuity
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME, BACKUP_DIR
from services.backup_service import backup_service
from services.auth_service import auth_service

class BackupView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=25, pady=20)
        self.content_frame.pack(fill="both", expand=True)

        self._build_top_actions()
        self._build_split_view()

    def _build_top_actions(self):
        card = tk.Frame(self.content_frame, bg="#FFFFFF", padx=18, pady=14, bd=1, relief="solid")
        card.config(highlightbackground=THEME["border"], highlightthickness=0)
        card.pack(fill="x", pady=(0, 15))

        tk.Label(
            card, text="💾 Database Backup & Disaster Recovery",
            font=(THEME["font_family"], 13, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]
        ).pack(side="left")

        btn_create = ttk.Button(card, text="➕ Create Live Backup Now", style="Success.TButton", command=self._create_backup)
        btn_create.pack(side="right")

    def _build_split_view(self):
        split = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        split.pack(fill="both", expand=True)

        # Left: Backup Files Treeview
        left = tk.Frame(split, bg="#FFFFFF", padx=15, pady=15, bd=1, relief="solid")
        left.config(highlightbackground=THEME["border"], highlightthickness=0)
        left.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Top Table Action
        l_top = tk.Frame(left, bg="#FFFFFF")
        l_top.pack(fill="x", pady=(0, 10))

        tk.Label(l_top, text="Available Database Snapshots", font=(THEME["font_family"], 11, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(side="left")

        btn_restore = ttk.Button(l_top, text="⚠️ Restore Selected Snapshot", style="Danger.TButton", command=self._restore_backup)
        btn_restore.pack(side="right")

        cols = ("filename", "size", "created", "type")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", style="Custom.Treeview")
        self.tree.heading("filename", text="Backup File Name", anchor="w")
        self.tree.heading("size", text="Size (KB)", anchor="e")
        self.tree.heading("created", text="Created At", anchor="w")
        self.tree.heading("type", text="Category", anchor="center")

        self.tree.column("filename", width=260)
        self.tree.column("size", width=80, anchor="e")
        self.tree.column("created", width=140)
        self.tree.column("type", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)

        # Right: Recovery Instructions & TQM Assurance Card
        right = tk.Frame(split, bg="#FFFFFF", padx=20, pady=18, bd=1, relief="solid", width=320)
        right.config(highlightbackground=THEME["border"], highlightthickness=0)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="Disaster Recovery Protocol", font=(THEME["font_family"], 11, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 10))

        instructions = (
            "1. Atomic Online Backup:\n"
            "   Backups use SQLite's native online backup API. The system continues servicing live vehicle movements without locking.\n\n"
            "2. Automated Pre-Validation:\n"
            "   Every newly created backup file is verified with PRAGMA integrity_check immediately after writing.\n\n"
            "3. Safety Snapshot Guarantee:\n"
            "   Prior to restoring any older backup, ParkSmart Pro automatically generates an emergency safety snapshot (pre_restore_safety_backup_*.db) of the active database.\n\n"
            "4. Self-Healing Rollback:\n"
            "   If a restored backup fails post-restore integrity checks, the system aborts and restores the safety snapshot."
        )

        lbl_inst = tk.Label(
            right, text=instructions, font=(THEME["font_family"], 8),
            bg="#FFFFFF", fg=THEME["text_muted"], justify="left", wraplength=280
        )
        lbl_inst.pack(anchor="w")

        tk.Frame(right, bg=THEME["border"], height=1).pack(fill="x", pady=15)

        lbl_dir = tk.Label(
            right, text=f"Storage Path:\n{BACKUP_DIR}",
            font=("Consolas", 7), bg="#FFFFFF", fg="#475569", justify="left", wraplength=280
        )
        lbl_dir.pack(anchor="w")

    def refresh_backups(self):
        backups = backup_service.list_backups()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for b in backups:
            cat_str = "Pre-Restore Safety" if b["is_safety"] else "Manual Backup"
            self.tree.insert("", "end", values=(
                b["filename"],
                f"{b['size_kb']} KB",
                b["created_at"],
                cat_str
            ))

    def _create_backup(self):
        user = auth_service.current_user
        uid = user.id if user else None
        uname = user.username if user else None

        ok, path, msg = backup_service.create_backup(user_id=uid, username=uname)
        if ok:
            messagebox.showinfo("Backup Completed", msg)
            self.refresh_backups()
        else:
            messagebox.showerror("Backup Failed", msg)

    def _restore_backup(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a backup file to restore.")
            return

        vals = self.tree.item(sel[0], "values")
        fname = vals[0]
        backup_file = BACKUP_DIR / fname

        confirm_msg = (
            f"Are you sure you want to restore database snapshot:\n'{fname}'?\n\n"
            "An automatic safety snapshot of the active database will be created before restoring."
        )

        if not messagebox.askyesno("Confirm Database Restore", confirm_msg, icon="warning"):
            return

        user = auth_service.current_user
        uid = user.id if user else None
        uname = user.username if user else None

        ok, msg = backup_service.restore_backup(backup_file, user_id=uid, username=uname)
        if ok:
            messagebox.showinfo("Restore Succeeded", msg)
            self.refresh_backups()
            self.on_navigate("dashboard")
        else:
            messagebox.showerror("Restore Failed", msg)
