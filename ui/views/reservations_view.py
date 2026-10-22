"""
ParkSmart Pro — Parking Reservation Management View
TQM Quality Attribute: Schedule Integrity & Proactive Resource Allocation
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from config import THEME, DEFAULT_VEHICLE_CATEGORIES
from services.reservation_service import reservation_service
from services.parking_service import parking_service
from services.auth_service import auth_service
from ui.components.dialogs import TicketDialog
from utils.formatters import get_status_style

class ReservationsView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        self.content_frame.pack(fill="both", expand=True)

        self._build_top_bar()
        self._build_main_split()

    def _build_top_bar(self):
        bar = tk.Frame(self.content_frame, bg="#FFFFFF", padx=16, pady=12, bd=1, relief="solid")
        bar.config(highlightbackground=THEME["border"], highlightthickness=0)
        bar.pack(fill="x", pady=(0, 12))

        tk.Label(bar, text="📅 Parking Reservations", font=(THEME["font_family"], 12, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(side="left", padx=(0, 20))

        # Status filter
        tk.Label(bar, text="Status:", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(side="left", padx=(0, 4))
        self.cb_status = ttk.Combobox(bar, values=["ALL", "CONFIRMED", "CHECKED_IN", "CANCELLED", "EXPIRED"],
                                      state="readonly", width=12)
        self.cb_status.current(0)
        self.cb_status.pack(side="left", padx=(0, 10))
        self.cb_status.bind("<<ComboboxSelected>>", lambda e: self.refresh_reservations())

        # Search box
        tk.Label(bar, text="Search:", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(side="left", padx=(0, 4))
        self.ent_search = ttk.Entry(bar, width=16)
        self.ent_search.pack(side="left", padx=(0, 8))
        self.ent_search.bind("<Return>", lambda e: self.refresh_reservations())

        btn_filter = ttk.Button(bar, text="Filter", style="Secondary.TButton", command=self.refresh_reservations)
        btn_filter.pack(side="left", padx=(0, 15))

    def _build_main_split(self):
        split = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        split.pack(fill="both", expand=True)

        # Left Column: New Reservation Booking Form
        left = tk.Frame(split, bg="#FFFFFF", padx=18, pady=16, bd=1, relief="solid", width=340)
        left.config(highlightbackground=THEME["border"], highlightthickness=0)
        left.pack(side="left", fill="y", padx=(0, 15))
        left.pack_propagate(False)

        tk.Label(left, text="Create Advance Reservation", font=(THEME["font_family"], 11, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 10))

        # Customer Name
        tk.Label(left, text="Customer Name *", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_name = ttk.Entry(left)
        self.ent_name.pack(fill="x", pady=(2, 8))

        # Phone
        tk.Label(left, text="Phone Number", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_phone = ttk.Entry(left)
        self.ent_phone.pack(fill="x", pady=(2, 8))

        # Vehicle Reg
        tk.Label(left, text="Vehicle Registration *", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_reg = ttk.Entry(left)
        self.ent_reg.pack(fill="x", pady=(2, 8))

        # Vehicle Category
        tk.Label(left, text="Vehicle Category *", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(anchor="w")
        cats = [c["code"] for c in DEFAULT_VEHICLE_CATEGORIES]
        self.cb_cat = ttk.Combobox(left, values=cats, state="readonly")
        self.cb_cat.current(1) # CAR
        self.cb_cat.pack(fill="x", pady=(2, 8))
        self.cb_cat.bind("<<ComboboxSelected>>", lambda e: self._populate_slot_options())

        # Start Time
        tk.Label(left, text="Start Datetime (YYYY-MM-DD HH:MM) *", font=(THEME["font_family"], 8, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_start = ttk.Entry(left)
        self.ent_start.pack(fill="x", pady=(2, 8))

        # End Time
        tk.Label(left, text="End Datetime (YYYY-MM-DD HH:MM) *", font=(THEME["font_family"], 8, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_end = ttk.Entry(left)
        self.ent_end.pack(fill="x", pady=(2, 8))

        # Assigned Slot
        tk.Label(left, text="Target Slot *", font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.cb_slot = ttk.Combobox(left, state="readonly")
        self.cb_slot.pack(fill="x", pady=(2, 14))

        # Submit Button
        btn_book = ttk.Button(left, text="Confirm Reservation ➔", style="Primary.TButton", command=self._submit_booking)
        btn_book.pack(fill="x", pady=(5, 0))

        # Right Column: Existing Reservations Table + Actions
        right = tk.Frame(split, bg="#FFFFFF", padx=15, pady=15, bd=1, relief="solid")
        right.config(highlightbackground=THEME["border"], highlightthickness=0)
        right.pack(side="right", fill="both", expand=True)

        # Table Header Actions
        r_top = tk.Frame(right, bg="#FFFFFF")
        r_top.pack(fill="x", pady=(0, 10))

        tk.Label(r_top, text="Active & Upcoming Bookings", font=(THEME["font_family"], 11, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(side="left")

        self.btn_cancel = ttk.Button(r_top, text="Cancel Booking", style="Danger.TButton", command=self._cancel_booking)
        self.btn_cancel.pack(side="right", padx=(5, 0))

        self.btn_checkin = ttk.Button(r_top, text="Check-In Vehicle", style="Success.TButton", command=self._checkin_booking)
        self.btn_checkin.pack(side="right")

        cols = ("id", "code", "customer", "phone", "reg", "cat", "slot", "start", "end", "status")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", style="Custom.Treeview")
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Code", anchor="w")
        self.tree.heading("customer", text="Customer", anchor="w")
        self.tree.heading("phone", text="Phone", anchor="w")
        self.tree.heading("reg", text="Vehicle Reg", anchor="w")
        self.tree.heading("cat", text="Category", anchor="w")
        self.tree.heading("slot", text="Slot", anchor="center")
        self.tree.heading("start", text="Start Time", anchor="w")
        self.tree.heading("end", text="End Time", anchor="w")
        self.tree.heading("status", text="Status", anchor="center")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("code", width=120)
        self.tree.column("customer", width=100)
        self.tree.column("phone", width=90)
        self.tree.column("reg", width=90)
        self.tree.column("cat", width=70)
        self.tree.column("slot", width=50, anchor="center")
        self.tree.column("start", width=120)
        self.tree.column("end", width=120)
        self.tree.column("status", width=80, anchor="center")

        self.tree.pack(fill="both", expand=True)

    def _populate_slot_options(self):
        cat = self.cb_cat.get()
        slots = parking_service.get_slots(category=cat, status="AVAILABLE")
        self.available_slots = slots
        opts = [f"{s.slot_code} ({s.zone_code or 'Z'})" for s in slots]
        self.cb_slot["values"] = opts
        if opts:
            self.cb_slot.current(0)
        else:
            self.cb_slot.set("No available bays")

    def refresh_reservations(self):
        # Set default start & end dates in form if empty
        now = datetime.now()
        if not self.ent_start.get():
            self.ent_start.insert(0, (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:00"))
        if not self.ent_end.get():
            self.ent_end.insert(0, (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:00"))

        self._populate_slot_options()

        status = self.cb_status.get()
        kw = self.ent_search.get().strip()
        records = reservation_service.get_reservations(status=status, search=kw)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in records:
            self.tree.insert("", "end", values=(
                r.id,
                r.reservation_code,
                r.customer_name,
                r.customer_phone or "-",
                r.vehicle_registration,
                r.vehicle_category,
                r.slot_code or "-",
                r.start_time,
                r.end_time,
                r.status
            ))

    def _submit_booking(self):
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        reg = self.ent_reg.get().strip()
        cat = self.cb_cat.get()
        start_t = self.ent_start.get().strip()
        end_t = self.ent_end.get().strip()

        if not hasattr(self, "available_slots") or not self.available_slots:
            messagebox.showerror("Error", "No available parking slots for this category.")
            return

        sel_idx = self.cb_slot.current()
        if sel_idx < 0 or sel_idx >= len(self.available_slots):
            messagebox.showerror("Error", "Please select a target slot.")
            return

        slot_id = self.available_slots[sel_idx].id
        user = auth_service.current_user
        uid = user.id if user else None
        uname = user.username if user else None

        ok, res, msg = reservation_service.create_reservation(
            customer_name=name,
            customer_phone=phone,
            vehicle_reg=reg,
            category=cat,
            slot_id=slot_id,
            start_time_str=start_t,
            end_time_str=end_t,
            user_id=uid,
            username=uname
        )

        if ok and res:
            messagebox.showinfo("Success", msg)
            self.ent_name.delete(0, tk.END)
            self.ent_phone.delete(0, tk.END)
            self.ent_reg.delete(0, tk.END)
            self.refresh_reservations()
        else:
            messagebox.showerror("Reservation Failed", msg)

    def _cancel_booking(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a reservation to cancel.")
            return
        vals = self.tree.item(sel[0], "values")
        res_id = int(vals[0])
        code = vals[1]

        if messagebox.askyesno("Confirm Cancellation", f"Cancel reservation #{code}?"):
            user = auth_service.current_user
            uid = user.id if user else None
            uname = user.username if user else None
            ok, msg = reservation_service.cancel_reservation(res_id, user_id=uid, username=uname)
            if ok:
                messagebox.showinfo("Cancelled", msg)
                self.refresh_reservations()
            else:
                messagebox.showerror("Error", msg)

    def _checkin_booking(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a confirmed reservation to check in.")
            return
        vals = self.tree.item(sel[0], "values")
        res_id, code, cust, phone, reg, cat, slot_code, s_time, e_time, status = vals

        if status != "CONFIRMED":
            messagebox.showerror("Error", f"Reservation is {status}. Only CONFIRMED bookings can be checked in.")
            return

        # Find slot id
        slots = parking_service.get_slots(search_code=slot_code)
        if not slots:
            messagebox.showerror("Error", f"Slot {slot_code} not found.")
            return

        slot_id = slots[0].id
        user = auth_service.current_user
        uid = user.id if user else None
        uname = user.username if user else None

        ok, session, msg = parking_service.register_vehicle_entry(
            vehicle_reg=reg,
            category=cat,
            slot_id=slot_id,
            user_id=uid,
            username=uname,
            notes=f"Check-in from Reservation #{code}"
        )

        if ok and session:
            # Mark reservation as CHECKED_IN
            from database.connection import get_db_connection
            conn = get_db_connection()
            conn.execute("UPDATE reservations SET status = 'CHECKED_IN' WHERE id = ?", (int(res_id),))
            conn.commit()
            conn.close()

            TicketDialog(self, {
                "ticket_number": session.ticket_number,
                "vehicle_registration": session.vehicle_registration,
                "vehicle_category": session.vehicle_category,
                "slot_code": session.slot_code,
                "zone_name": session.zone_name,
                "entry_time": session.entry_time
            })
            self.refresh_reservations()
        else:
            messagebox.showerror("Check-in Error", msg)
