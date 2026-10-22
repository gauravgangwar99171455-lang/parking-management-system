"""
ParkSmart Pro — Robust CSV Import & Export View
TQM Quality Attribute: Prevention Rather Than Correction (Pre-Validation & Diagnostics)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from config import THEME, TEMPLATES_DIR, REPORTS_DIR
from services.import_service import import_service
from services.auth_service import auth_service
from services.parking_service import parking_service
from services.search_service import search_service
from utils.export_helpers import export_rows_to_csv

class ImportsView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.preview_result = None

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        self.content_frame.pack(fill="both", expand=True)

        self._build_top_actions()
        self._build_preview_panel()

    def _build_top_actions(self):
        card = tk.Frame(self.content_frame, bg="#FFFFFF", padx=16, pady=14, bd=1, relief="solid")
        card.config(highlightbackground=THEME["border"], highlightthickness=0)
        card.pack(fill="x", pady=(0, 15))

        tk.Label(card, text="📂 CSV Data Import & Export Engine",
                 font=(THEME["font_family"], 12, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]).pack(side="left", padx=(0, 20))

        # Import Type
        tk.Label(card, text="Import Type:", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(side="left", padx=(0, 4))
        self.cb_type = ttk.Combobox(card, values=["PARKING_SLOTS", "HISTORICAL_SESSIONS"], state="readonly", width=22)
        self.cb_type.current(0)
        self.cb_type.pack(side="left", padx=(0, 12))

        # Select File Button
        btn_browse = ttk.Button(card, text="📁 Select CSV File & Validate", style="Primary.TButton", command=self._select_and_validate)
        btn_browse.pack(side="left", padx=(0, 10))

        # Sample Template Button
        btn_tmpl = ttk.Button(card, text="📄 Get Sample Template", style="Secondary.TButton", command=self._open_sample_template)
        btn_tmpl.pack(side="left", padx=(0, 15))

        # Export All Button (Right)
        btn_exp_inv = ttk.Button(card, text="📥 Export Slots Inventory", style="Secondary.TButton", command=self._export_slots_inventory)
        btn_exp_inv.pack(side="right")

    def _build_preview_panel(self):
        self.preview_card = tk.Frame(self.content_frame, bg="#FFFFFF", padx=16, pady=14, bd=1, relief="solid")
        self.preview_card.config(highlightbackground=THEME["border"], highlightthickness=0)
        self.preview_card.pack(fill="both", expand=True)

        # Pre-Validation Diagnostic Bar
        diag_row = tk.Frame(self.preview_card, bg="#FFFFFF")
        diag_row.pack(fill="x", pady=(0, 10))

        self.lbl_status = tk.Label(
            diag_row, text="No CSV file selected. Choose a CSV file above to run diagnostic pre-validation.",
            font=(THEME["font_family"], 10, "bold"), bg="#FFFFFF", fg=THEME["text_muted"]
        )
        self.lbl_status.pack(side="left")

        self.btn_commit = ttk.Button(
            diag_row, text="Confirm & Import Valid Records ➔",
            style="Success.TButton", state="disabled", command=self._commit_import
        )
        self.btn_commit.pack(side="right")

        # Diagnostics Badges
        self.badge_frame = tk.Frame(self.preview_card, bg="#FFFFFF")
        self.badge_frame.pack(fill="x", pady=(0, 10))

        self.lbl_valid_badge = tk.Label(self.badge_frame, text="Valid Rows: 0", font=(THEME["font_family"], 9, "bold"),
                                        bg="#DCFCE7", fg="#166534", padx=8, pady=3)
        self.lbl_valid_badge.pack(side="left", padx=(0, 8))

        self.lbl_invalid_badge = tk.Label(self.badge_frame, text="Invalid Rows: 0", font=(THEME["font_family"], 9, "bold"),
                                          bg="#FEE2E2", fg="#991B1B", padx=8, pady=3)
        self.lbl_invalid_badge.pack(side="left")

        # Diagnostics Error Treeview
        tk.Label(self.preview_card, text="Row-Level Validation Diagnostics & Error Explanations:",
                 font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(8, 4))

        cols = ("row", "data", "status", "reasons")
        self.tree_diag = ttk.Treeview(self.preview_card, columns=cols, show="headings", style="Custom.Treeview")
        self.tree_diag.heading("row", text="Row #", anchor="center")
        self.tree_diag.heading("data", text="Record Data", anchor="w")
        self.tree_diag.heading("status", text="Validation State", anchor="center")
        self.tree_diag.heading("reasons", text="Errors / Rejection Diagnostics", anchor="w")

        self.tree_diag.column("row", width=60, anchor="center")
        self.tree_diag.column("data", width=250)
        self.tree_diag.column("status", width=120, anchor="center")
        self.tree_diag.column("reasons", width=380)

        self.tree_diag.pack(fill="both", expand=True)

    def _select_and_validate(self):
        filepath = filedialog.askopenfilename(
            initialdir=str(TEMPLATES_DIR),
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        import_type = self.cb_type.get()
        self.current_file = Path(filepath)

        if import_type == "PARKING_SLOTS":
            res = import_service.validate_slot_csv(self.current_file)
        else:
            res = import_service.validate_historical_sessions_csv(self.current_file)

        if not res.get("success"):
            messagebox.showerror("Pre-Validation Failed", res.get("error", "Unknown validation error."))
            return

        self.preview_result = res

        # Clear diagnostic tree
        for item in self.tree_diag.get_children():
            self.tree_diag.delete(item)

        valid_cnt = res["valid_count"]
        invalid_cnt = res["invalid_count"]
        total = res["total_rows"]

        self.lbl_status.config(
            text=f"Validation Complete for '{self.current_file.name}': {valid_cnt} valid, {invalid_cnt} invalid out of {total} rows.",
            fg=THEME["success"] if invalid_cnt == 0 else THEME["warning"]
        )
        self.lbl_valid_badge.config(text=f"✓ Valid: {valid_cnt}")
        self.lbl_invalid_badge.config(text=f"✖ Rejected: {invalid_cnt}")

        # Show invalid rows first
        for inv in res["invalid_rows"]:
            self.tree_diag.insert("", "end", values=(
                inv["row_number"],
                str(inv["data"]),
                "REJECTED",
                inv["reasons"]
            ))

        # Show valid rows
        for v in res["valid_rows"]:
            self.tree_diag.insert("", "end", values=(
                v["row_number"],
                str(v),
                "VALID",
                "Ready for database insert"
            ))

        self.btn_commit.config(state="normal" if valid_cnt > 0 else "disabled")

    def _commit_import(self):
        if not self.preview_result or not self.preview_result.get("valid_rows"):
            return

        user = auth_service.current_user
        uid = user.id if user else None
        uname = user.username if user else None
        import_type = self.cb_type.get()

        valid_rows = self.preview_result["valid_rows"]
        fname = self.current_file.name

        if import_type == "PARKING_SLOTS":
            ok, msg = import_service.commit_slot_import(valid_rows, fname, user_id=uid, username=uname)
        else:
            ok, msg = import_service.commit_historical_import(valid_rows, fname, user_id=uid, username=uname)

        if ok:
            messagebox.showinfo("Import Success", msg)
            self.btn_commit.config(state="disabled")
            self.lbl_status.config(text=f"✓ {msg}", fg=THEME["success"])
        else:
            messagebox.showerror("Import Error", msg)

    def _open_sample_template(self):
        import_type = self.cb_type.get()
        if import_type == "PARKING_SLOTS":
            tmpl = TEMPLATES_DIR / "sample_slots.csv"
        else:
            tmpl = TEMPLATES_DIR / "sample_historical_sessions.csv"

        if tmpl.exists():
            messagebox.showinfo("Sample Template Available", f"Sample template is located at:\n{tmpl}\n\nYou can inspect or copy this file.")
        else:
            messagebox.showwarning("Not Found", f"Template not found at: {tmpl}")

    def _export_slots_inventory(self):
        filename = f"parksmart_slots_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        dest_path = filedialog.asksaveasfilename(
            initialdir=str(REPORTS_DIR),
            initialfile=filename,
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not dest_path:
            return

        slots = parking_service.get_slots()
        headers = ["Slot Code", "Zone Code", "Floor", "Vehicle Category", "Status", "Current Vehicle", "Current Ticket"]
        rows = [
            [s.slot_code, s.zone_code or "", s.floor_number, s.supported_category, s.status, s.current_vehicle or "", s.current_ticket or ""]
            for s in slots
        ]

        ok, msg = export_rows_to_csv(Path(dest_path), headers, rows)
        if ok:
            messagebox.showinfo("Export Success", msg)
        else:
            messagebox.showerror("Export Failed", msg)
