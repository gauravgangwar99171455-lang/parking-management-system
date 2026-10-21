"""
ParkSmart Pro — Parking Slot Management & Visualization View
TQM Quality Attribute: Visual Control (Poka-Yoke / Error Proofing)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME
from services.parking_service import parking_service
from services.auth_service import auth_service
from ui.components.dialogs import AddSlotDialog
from utils.formatters import get_status_style

CATEGORY_ICONS = {
    "CAR": "🚗",
    "TWO_WHEELER": "🏍️",
    "SUV": "🚙",
    "COMMERCIAL": "🚚",
    "EV": "⚡",
}

class SlotsView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.selected_zone_id = None
        self.selected_status = "ALL"
        self.selected_category = "ALL"

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        self.content_frame.pack(fill="both", expand=True)

        # Header & Filter Toolbar
        self._build_toolbar()

        # Visual Slots Grid Container (Scrollable canvas)
        self._build_grid_canvas()

    def _build_toolbar(self):
        bar = tk.Frame(self.content_frame, bg="#FFFFFF", padx=15, pady=12, bd=1, relief="solid")
        bar.config(highlightbackground=THEME["border"], highlightthickness=0)
        bar.pack(fill="x", pady=(0, 15))

        # Title
        tk.Label(bar, text="🅿️ Slot Inventory", font=(THEME["font_family"], 12, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(side="left", padx=(0, 15))

        # Zone Filter Dropdown
        tk.Label(bar, text="Zone:", bg="#FFFFFF", font=(THEME["font_family"], 9, "bold")).pack(side="left", padx=(0, 4))
        self.cb_zone = ttk.Combobox(bar, state="readonly", width=18)
        self.cb_zone.pack(side="left", padx=(0, 12))
        self.cb_zone.bind("<<ComboboxSelected>>", lambda e: self.refresh_slots())

        # Status Filter Dropdown
        tk.Label(bar, text="Status:", bg="#FFFFFF", font=(THEME["font_family"], 9, "bold")).pack(side="left", padx=(0, 4))
        self.cb_status = ttk.Combobox(
            bar, values=["ALL", "AVAILABLE", "OCCUPIED", "RESERVED", "MAINTENANCE"],
            state="readonly", width=12
        )
        self.cb_status.current(0)
        self.cb_status.pack(side="left", padx=(0, 12))
        self.cb_status.bind("<<ComboboxSelected>>", lambda e: self.refresh_slots())

        # Category Filter Dropdown
        tk.Label(bar, text="Type:", bg="#FFFFFF", font=(THEME["font_family"], 9, "bold")).pack(side="left", padx=(0, 4))
        self.cb_cat = ttk.Combobox(
            bar, values=["ALL", "CAR", "TWO_WHEELER", "SUV", "COMMERCIAL", "EV"],
            state="readonly", width=12
        )
        self.cb_cat.current(0)
        self.cb_cat.pack(side="left", padx=(0, 15))
        self.cb_cat.bind("<<ComboboxSelected>>", lambda e: self.refresh_slots())

        # Search by Slot Code
        tk.Label(bar, text="Search:", bg="#FFFFFF", font=(THEME["font_family"], 9, "bold")).pack(side="left", padx=(0, 4))
        self.ent_search = ttk.Entry(bar, width=10)
        self.ent_search.pack(side="left", padx=(0, 6))
        self.ent_search.bind("<Return>", lambda e: self.refresh_slots())

        btn_find = ttk.Button(bar, text="Filter", style="Secondary.TButton", command=self.refresh_slots)
        btn_find.pack(side="left", padx=(0, 15))

        # Add Slot Button (Right aligned)
        self.btn_add = ttk.Button(bar, text="+ Add Slot", style="Primary.TButton", command=self._open_add_slot)
        self.btn_add.pack(side="right")

    def _build_grid_canvas(self):
        outer = tk.Frame(self.content_frame, bg="#FFFFFF", bd=1, relief="solid")
        outer.config(highlightbackground=THEME["border"], highlightthickness=0)
        outer.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(outer, bg="#FFFFFF", bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#FFFFFF", padx=15, pady=15)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Resize window with canvas
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

    def refresh_slots(self):
        """Reload zones and slots according to active filter criteria."""
        # 1. Populate Zone dropdown if empty
        zones = parking_service.get_zones()
        zone_opts = ["ALL ZONES"] + [f"{z.code} — {z.name}" for z in zones]
        current_val = self.cb_zone.get()
        self.cb_zone["values"] = zone_opts
        if not current_val or current_val not in zone_opts:
            self.cb_zone.current(0)

        # 2. Extract selected filter values
        sel_zone_str = self.cb_zone.get()
        zone_id = None
        if sel_zone_str and sel_zone_str != "ALL ZONES":
            z_code = sel_zone_str.split(" — ")[0]
            matched = [z for z in zones if z.code == z_code]
            if matched:
                zone_id = matched[0].id

        status = self.cb_status.get()
        category = self.cb_cat.get()
        search_kw = self.ent_search.get().strip()

        # 3. Query slots
        slots = parking_service.get_slots(
            zone_id=zone_id,
            category=category,
            status=status,
            search_code=search_kw
        )

        # 4. Clear existing cards
        for w in self.scrollable_frame.winfo_children():
            w.destroy()

        if not slots:
            lbl_empty = tk.Label(
                self.scrollable_frame, text="No parking slots found matching the criteria.",
                font=(THEME["font_family"], 11), bg="#FFFFFF", fg=THEME["text_muted"]
            )
            lbl_empty.pack(pady=40)
            return

        # 5. Render Grid of Slots (5 columns per row)
        cols_per_row = 6
        for idx, s in enumerate(slots):
            r = idx // cols_per_row
            c = idx % cols_per_row
            self._render_slot_card(self.scrollable_frame, s, r, c)

    def _render_slot_card(self, parent, slot, row: int, col: int):
        style = get_status_style(slot.status)
        icon = CATEGORY_ICONS.get(slot.supported_category, "🚗")

        card = tk.Frame(parent, bg="#FFFFFF", bd=1, relief="solid", padx=10, pady=8, cursor="hand2")
        card.config(highlightbackground=THEME["border"], highlightthickness=0)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        # Top Row: Slot Code & Status Dot
        top_row = tk.Frame(card, bg="#FFFFFF")
        top_row.pack(fill="x")

        lbl_code = tk.Label(top_row, text=slot.slot_code, font=(THEME["font_family"], 10, "bold"),
                            bg="#FFFFFF", fg=THEME["text_dark"])
        lbl_code.pack(side="left")

        lbl_status = tk.Label(top_row, text=style["label"], font=(THEME["font_family"], 7, "bold"),
                              bg=style["bg"], fg=style["fg"], padx=4, pady=1)
        lbl_status.pack(side="right")

        # Center: Category Icon + Name
        lbl_icon = tk.Label(card, text=f"{icon}  {slot.supported_category}",
                            font=(THEME["font_family"], 8), bg="#FFFFFF", fg=THEME["text_muted"])
        lbl_icon.pack(anchor="w", pady=(4, 2))

        # Bottom info: If occupied, show ticket/vehicle
        if slot.status == "OCCUPIED" and slot.current_vehicle:
            lbl_veh = tk.Label(card, text=f"🚘 {slot.current_vehicle}",
                               font=("Consolas", 8, "bold"), bg="#FFFFFF", fg=THEME["danger"])
            lbl_veh.pack(anchor="w")
        else:
            lbl_loc = tk.Label(card, text=f"Floor {slot.floor_number}",
                               font=(THEME["font_family"], 7), bg="#FFFFFF", fg="#94A3B8")
            lbl_loc.pack(anchor="w")

        # Click event to toggle / manage slot
        card.bind("<Button-1>", lambda e, s=slot: self._on_slot_click(s))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, s=slot: self._on_slot_click(s))

    def _on_slot_click(self, slot):
        """Slot click action menu."""
        msg = f"Slot: {slot.slot_code}\nZone: {slot.zone_name or slot.zone_code}\nType: {slot.supported_category}\nStatus: {slot.status}"
        if slot.status == "OCCUPIED" and slot.current_vehicle:
            msg += f"\nActive Ticket: {slot.current_ticket}\nVehicle: {slot.current_vehicle}\nEntry: {slot.current_entry_time}"

        user = auth_service.current_user
        if not user or not user.is_admin():
            messagebox.showinfo(f"Slot {slot.slot_code} Details", msg)
            return

        # If Admin, allow Maintenance toggle
        if slot.status == "AVAILABLE":
            if messagebox.askyesno("Slot Status Change", f"{msg}\n\nMark slot {slot.slot_code} as Under Maintenance?"):
                parking_service.update_slot_status(slot.id, "MAINTENANCE")
                self.refresh_slots()
        elif slot.status == "MAINTENANCE":
            if messagebox.askyesno("Slot Status Change", f"{msg}\n\nRestore slot {slot.slot_code} to AVAILABLE?"):
                parking_service.update_slot_status(slot.id, "AVAILABLE")
                self.refresh_slots()
        else:
            messagebox.showinfo(f"Slot {slot.slot_code} Details", msg)

    def _open_add_slot(self):
        zones = parking_service.get_zones()
        if not zones:
            messagebox.showerror("Error", "No parking zones exist.")
            return

        def handle_add(code, zone_id, cat, dlg):
            ok, msg = parking_service.add_slot(code, zone_id, cat)
            if ok:
                messagebox.showinfo("Success", msg)
                dlg.destroy()
                self.refresh_slots()
            else:
                messagebox.showerror("Error", msg)

        AddSlotDialog(self, zones, handle_add)
