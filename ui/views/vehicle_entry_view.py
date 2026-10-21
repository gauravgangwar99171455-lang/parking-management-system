"""
ParkSmart Pro — Vehicle Entry Registration View
TQM Quality Attribute: Error Proofing (Poka-Yoke) & Fast Inflow Throughput
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from config import THEME, DEFAULT_VEHICLE_CATEGORIES
from services.parking_service import parking_service
from services.auth_service import auth_service
from ui.components.dialogs import TicketDialog
from utils.validators import validate_reg_number, sanitize_reg_number

class VehicleEntryView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=25, pady=20)
        self.content_frame.pack(fill="both", expand=True)

        # Main Layout: 2 Columns (Left: Registration Form, Right: Live Available Slots & Recent Inflow)
        self.left_col = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))

        self.right_col = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        self.right_col.pack(side="right", fill="both", expand=True)

        self._build_entry_form()
        self._build_right_panel()

    def _build_entry_form(self):
        card = tk.Frame(self.left_col, bg="#FFFFFF", padx=25, pady=22, bd=1, relief="solid")
        card.config(highlightbackground=THEME["border"], highlightthickness=0)
        card.pack(fill="x")

        # Title
        tk.Label(
            card, text="📥 Vehicle Check-In & Ticket Issuance",
            font=(THEME["font_family"], 13, "bold"),
            bg="#FFFFFF", fg=THEME["text_dark"]
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            card, text="Enter vehicle license plate and allocate an eligible bay.",
            font=(THEME["font_family"], 8),
            bg="#FFFFFF", fg=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 18))

        # 1. Vehicle Registration Plate
        tk.Label(card, text="Vehicle Registration Number *", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_reg = ttk.Entry(card, font=("Consolas", 12, "bold"))
        self.ent_reg.pack(fill="x", pady=(3, 4))
        self.ent_reg.bind("<KeyRelease>", self._on_reg_typing)

        self.lbl_reg_feedback = tk.Label(
            card, text="e.g. KA-01-AB-1234 or DL-04-C-9999",
            font=(THEME["font_family"], 8), bg="#FFFFFF", fg=THEME["text_muted"]
        )
        self.lbl_reg_feedback.pack(anchor="w", pady=(0, 12))

        # 2. Vehicle Category
        tk.Label(card, text="Vehicle Category *", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w")

        cat_names = [f"{c['icon']}  {c['name']} ({c['code']})" for c in DEFAULT_VEHICLE_CATEGORIES]
        self.cb_category = ttk.Combobox(card, values=cat_names, state="readonly", font=(THEME["font_family"], 10))
        self.cb_category.current(1) # Default to Car
        self.cb_category.pack(fill="x", pady=(3, 14))
        self.cb_category.bind("<<ComboboxSelected>>", lambda e: self._update_eligible_slots())

        # 3. Slot Allocation Mode
        tk.Label(card, text="Slot Allocation *", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w")

        self.slot_var = tk.StringVar(value="AUTO")
        slot_mode_frame = tk.Frame(card, bg="#FFFFFF")
        slot_mode_frame.pack(fill="x", pady=(3, 6))

        tk.Radiobutton(
            slot_mode_frame, text="Auto-Assign Optimal Slot (Recommended)",
            variable=self.slot_var, value="AUTO", bg="#FFFFFF", font=(THEME["font_family"], 9),
            command=self._toggle_slot_dropdown
        ).pack(anchor="w")

        tk.Radiobutton(
            slot_mode_frame, text="Select Specific Slot Manually",
            variable=self.slot_var, value="MANUAL", bg="#FFFFFF", font=(THEME["font_family"], 9),
            command=self._toggle_slot_dropdown
        ).pack(anchor="w")

        self.cb_slots = ttk.Combobox(card, state="disabled", font=(THEME["font_family"], 9))
        self.cb_slots.pack(fill="x", pady=(2, 14))

        # 4. Optional Driver Note / Phone
        tk.Label(card, text="Driver Notes / Remarks (Optional)", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_notes = ttk.Entry(card)
        self.ent_notes.pack(fill="x", pady=(3, 18))

        # Submit Button
        self.btn_submit = ttk.Button(
            card, text="Generate Admission Ticket & Open Barrier ➔",
            style="Success.TButton",
            command=self._submit_entry,
            cursor="hand2"
        )
        self.btn_submit.pack(fill="x", ipady=4)

    def _build_right_panel(self):
        # Top Card: Live Eligible Slots Count
        self.card_avail = tk.Frame(self.right_col, bg="#FFFFFF", padx=18, pady=15, bd=1, relief="solid")
        self.card_avail.config(highlightbackground=THEME["border"], highlightthickness=0)
        self.card_avail.pack(fill="x", pady=(0, 15))

        self.lbl_avail_count = tk.Label(
            self.card_avail, text="Available Bays: Checking...",
            font=(THEME["font_family"], 11, "bold"), bg="#FFFFFF", fg=THEME["primary"]
        )
        self.lbl_avail_count.pack(anchor="w")

        self.lbl_avail_sub = tk.Label(
            self.card_avail, text="Eligible bays ready for entry",
            font=(THEME["font_family"], 8), bg="#FFFFFF", fg=THEME["text_muted"]
        )
        self.lbl_avail_sub.pack(anchor="w")

        # Bottom Card: Today's Recent Check-ins
        rec_card = tk.Frame(self.right_col, bg="#FFFFFF", padx=15, pady=12, bd=1, relief="solid")
        rec_card.config(highlightbackground=THEME["border"], highlightthickness=0)
        rec_card.pack(fill="both", expand=True)

        tk.Label(
            rec_card, text="Recent Check-Ins (Active Sessions)",
            font=(THEME["font_family"], 10, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]
        ).pack(anchor="w", pady=(0, 8))

        cols = ("tkt", "reg", "cat", "slot", "time")
        self.tree_active = ttk.Treeview(rec_card, columns=cols, show="headings", style="Custom.Treeview", height=10)
        self.tree_active.heading("tkt", text="Ticket #", anchor="w")
        self.tree_active.heading("reg", text="Vehicle Reg", anchor="w")
        self.tree_active.heading("cat", text="Category", anchor="w")
        self.tree_active.heading("slot", text="Slot", anchor="center")
        self.tree_active.heading("time", text="Entry Time", anchor="w")

        self.tree_active.column("tkt", width=120)
        self.tree_active.column("reg", width=100)
        self.tree_active.column("cat", width=80)
        self.tree_active.column("slot", width=60, anchor="center")
        self.tree_active.column("time", width=120)

        self.tree_active.pack(fill="both", expand=True)

    def _get_selected_category_code(self) -> str:
        idx = self.cb_category.current()
        if 0 <= idx < len(DEFAULT_VEHICLE_CATEGORIES):
            return DEFAULT_VEHICLE_CATEGORIES[idx]["code"]
        return "CAR"

    def _on_reg_typing(self, event):
        reg = self.ent_reg.get().strip().upper()
        if not reg:
            self.lbl_reg_feedback.config(text="e.g. KA-01-AB-1234 or DL-04-C-9999", fg=THEME["text_muted"])
            return

        is_valid, msg = validate_reg_number(reg)
        if is_valid:
            self.lbl_reg_feedback.config(text="✓ Valid registration plate format", fg=THEME["success"])
        else:
            self.lbl_reg_feedback.config(text=f"⚠️ {msg}", fg=THEME["danger"])

    def _toggle_slot_dropdown(self):
        if self.slot_var.get() == "MANUAL":
            self.cb_slots.config(state="readonly")
            self._update_eligible_slots()
        else:
            self.cb_slots.config(state="disabled")

    def _update_eligible_slots(self):
        cat = self._get_selected_category_code()
        eligible = parking_service.find_eligible_slots(cat)

        self.eligible_slots = eligible
        self.lbl_avail_count.config(text=f"Available {cat} Bays: {len(eligible)}")

        opts = [f"{s.slot_code} (Floor {s.floor_number} - {s.zone_name or s.zone_code})" for s in eligible]
        self.cb_slots["values"] = opts
        if opts:
            self.cb_slots.current(0)
        else:
            self.cb_slots.set("No available slots")

    def refresh_view(self):
        self._update_eligible_slots()
        self.ent_reg.delete(0, tk.END)
        self.ent_notes.delete(0, tk.END)
        self.lbl_reg_feedback.config(text="e.g. KA-01-AB-1234 or DL-04-C-9999", fg=THEME["text_muted"])

        # Populate active sessions table
        slots = parking_service.get_slots(status="OCCUPIED")
        for item in self.tree_active.get_children():
            self.tree_active.delete(item)

        for s in slots[:12]:
            self.tree_active.insert("", "end", values=(
                s.current_ticket or "-",
                s.current_vehicle or "-",
                s.supported_category,
                s.slot_code,
                s.current_entry_time or "-"
            ))

    def _submit_entry(self):
        raw_reg = self.ent_reg.get().strip()
        is_ok, msg = validate_reg_number(raw_reg)
        if not is_ok:
            messagebox.showerror("Validation Error", msg)
            self.ent_reg.focus_set()
            return

        category = self._get_selected_category_code()
        slot_id = None
        if self.slot_var.get() == "MANUAL":
            sel_idx = self.cb_slots.current()
            if sel_idx < 0 or sel_idx >= len(self.eligible_slots):
                messagebox.showerror("Error", "Please select a valid parking slot from the dropdown.")
                return
            slot_id = self.eligible_slots[sel_idx].id

        notes = self.ent_notes.get().strip()
        user = auth_service.current_user
        uid = user.id if user else None
        uname = user.username if user else None

        ok, session, res_msg = parking_service.register_vehicle_entry(
            vehicle_reg=raw_reg,
            category=category,
            slot_id=slot_id,
            user_id=uid,
            username=uname,
            notes=notes
        )

        if ok and session:
            # Open Ticket Dialog
            TicketDialog(self, {
                "ticket_number": session.ticket_number,
                "vehicle_registration": session.vehicle_registration,
                "vehicle_category": session.vehicle_category,
                "slot_code": session.slot_code,
                "zone_name": session.zone_name,
                "entry_time": session.entry_time
            })
            self.refresh_view()
        else:
            messagebox.showerror("Entry Failed", res_msg)
