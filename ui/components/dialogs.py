"""
ParkSmart Pro — Modern Modal Dialogs (Ticket, Receipt, Confirmations)
TQM Quality Attribute: Usability & Error Prevention
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME, CURRENCY_SYMBOL
from utils.formatters import format_currency

class TicketDialog(tk.Toplevel):
    def __init__(self, parent, session_data: dict):
        super().__init__(parent)
        self.title("Parking Ticket Generated — ParkSmart Pro")
        self.geometry("400x520")
        self.resizable(False, False)
        self.configure(bg=THEME["bg_main"])
        self.transient(parent)
        self.grab_set()

        # Ticket Card Container
        card = tk.Frame(self, bg="#FFFFFF", bd=1, relief="solid", highlightthickness=0)
        card.config(highlightbackground=THEME["border"])
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        lbl_brand = tk.Label(card, text="PARKSMART PRO", font=(THEME["font_family"], 13, "bold"),
                             bg="#FFFFFF", fg=THEME["primary"])
        lbl_brand.pack(pady=(15, 2))

        lbl_sub = tk.Label(card, text="OFFICIAL PARKING ADMISSION TICKET", font=(THEME["font_family"], 8),
                           bg="#FFFFFF", fg=THEME["text_muted"])
        lbl_sub.pack(pady=(0, 10))

        # Divider
        tk.Frame(card, bg=THEME["border"], height=1).pack(fill="x", padx=15, pady=5)

        # Barcode Simulation
        lbl_barcode = tk.Label(
            card,
            text="||| | |||| | ||| |||| | || ||| |||| |",
            font=("Consolas", 16, "bold"),
            bg="#FFFFFF", fg=THEME["text_dark"]
        )
        lbl_barcode.pack(pady=4)

        lbl_tkt_num = tk.Label(
            card, text=session_data.get("ticket_number", ""),
            font=("Consolas", 12, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]
        )
        lbl_tkt_num.pack(pady=(0, 10))

        # Details Grid
        details = [
            ("Vehicle Registration:", session_data.get("vehicle_registration", "")),
            ("Vehicle Category:", session_data.get("vehicle_category", "")),
            ("Allocated Slot:", session_data.get("slot_code", "")),
            ("Zone Location:", session_data.get("zone_name", "General")),
            ("Entry Timestamp:", session_data.get("entry_time", "")),
        ]

        grid_frame = tk.Frame(card, bg="#FFFFFF", padx=20)
        grid_frame.pack(fill="x", pady=5)

        for i, (k, v) in enumerate(details):
            tk.Label(grid_frame, text=k, font=(THEME["font_family"], 9, "bold"),
                     bg="#FFFFFF", fg=THEME["text_muted"], anchor="w").grid(row=i, column=0, sticky="w", pady=4)
            tk.Label(grid_frame, text=v, font=(THEME["font_family"], 9),
                     bg="#FFFFFF", fg=THEME["text_dark"], anchor="e").grid(row=i, column=1, sticky="e", pady=4)

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # Instructions / Policy
        policy = "Please retain this ticket. Loss of ticket incurs standard penalty fee.\nSpeed limit inside parking bays is 10 km/h."
        lbl_policy = tk.Label(card, text=policy, font=(THEME["font_family"], 7),
                              bg="#FFFFFF", fg=THEME["text_muted"], justify="center")
        lbl_policy.pack(pady=(15, 10))

        # Bottom Buttons
        btn_frame = tk.Frame(self, bg=THEME["bg_main"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        btn_print = ttk.Button(btn_frame, text="🖨️ Print Ticket", style="Primary.TButton", command=self._mock_print)
        btn_print.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_close = ttk.Button(btn_frame, text="Close", style="Secondary.TButton", command=self.destroy)
        btn_close.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _mock_print(self):
        messagebox.showinfo("Print Command", "Ticket sent to default thermal printer spooler successfully!")
        self.destroy()

class ReceiptDialog(tk.Toplevel):
    def __init__(self, parent, receipt_data: dict):
        super().__init__(parent)
        self.title("Parking Receipt — ParkSmart Pro")
        self.geometry("420x560")
        self.resizable(False, False)
        self.configure(bg=THEME["bg_main"])
        self.transient(parent)
        self.grab_set()

        card = tk.Frame(self, bg="#FFFFFF", bd=1, relief="solid", highlightthickness=0)
        card.config(highlightbackground=THEME["border"])
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        lbl_brand = tk.Label(card, text="PARKSMART PRO", font=(THEME["font_family"], 13, "bold"),
                             bg="#FFFFFF", fg=THEME["success"])
        lbl_brand.pack(pady=(15, 2))

        lbl_sub = tk.Label(card, text="OFFICIAL PARKING PAYMENT RECEIPT", font=(THEME["font_family"], 8),
                           bg="#FFFFFF", fg=THEME["text_muted"])
        lbl_sub.pack(pady=(0, 10))

        # Divider
        tk.Frame(card, bg=THEME["border"], height=1).pack(fill="x", padx=15, pady=5)

        # Receipt Rows
        details = [
            ("Receipt / Txn Ref:", receipt_data.get("transaction_reference", "-")),
            ("Ticket Number:", receipt_data.get("ticket_number", "-")),
            ("Vehicle Reg:", receipt_data.get("vehicle_registration", "-")),
            ("Vehicle Type:", receipt_data.get("vehicle_category", "-")),
            ("Entry Time:", receipt_data.get("entry_time", "-")),
            ("Exit Time:", receipt_data.get("exit_time", "-")),
            ("Total Duration:", receipt_data.get("duration_formatted", "-")),
            ("Gross Amount:", format_currency(receipt_data.get("gross_cents", 0))),
            ("Discount Applied:", f"-{format_currency(receipt_data.get('discount_cents', 0))}"),
            ("NET AMOUNT PAID:", format_currency(receipt_data.get("net_cents", 0))),
            ("Payment Mode:", receipt_data.get("payment_method", "CASH")),
            ("Attendant / Cashier:", receipt_data.get("cashier_name", "System")),
        ]

        grid_frame = tk.Frame(card, bg="#FFFFFF", padx=20)
        grid_frame.pack(fill="x", pady=5)

        for i, (k, v) in enumerate(details):
            is_bold = "NET" in k or "Paid" in k
            fg_col = THEME["success"] if "NET" in k else THEME["text_dark"]
            tk.Label(grid_frame, text=k, font=(THEME["font_family"], 9, "bold" if is_bold else "normal"),
                     bg="#FFFFFF", fg=THEME["text_muted"] if not is_bold else THEME["text_dark"],
                     anchor="w").grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(grid_frame, text=v, font=(THEME["font_family"], 9, "bold" if is_bold else "normal"),
                     bg="#FFFFFF", fg=fg_col, anchor="e").grid(row=i, column=1, sticky="e", pady=3)

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # Thank you note
        lbl_thanks = tk.Label(card, text="Thank you for parking with ParkSmart Pro!\nDrive safely and visit again.",
                              font=(THEME["font_family"], 8), bg="#FFFFFF", fg=THEME["text_muted"], justify="center")
        lbl_thanks.pack(pady=(15, 10))

        # Bottom Buttons
        btn_frame = tk.Frame(self, bg=THEME["bg_main"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        btn_print = ttk.Button(btn_frame, text="🖨️ Print Receipt", style="Success.TButton", command=self._mock_print)
        btn_print.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_close = ttk.Button(btn_frame, text="Close", style="Secondary.TButton", command=self.destroy)
        btn_close.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _mock_print(self):
        messagebox.showinfo("Print Command", "Receipt printed successfully!")
        self.destroy()

class AddSlotDialog(tk.Toplevel):
    def __init__(self, parent, zones: list, on_slot_added):
        super().__init__(parent)
        self.title("Add New Parking Slot")
        self.geometry("380x300")
        self.resizable(False, False)
        self.configure(bg=THEME["bg_main"])
        self.transient(parent)
        self.grab_set()

        self.on_slot_added = on_slot_added
        self.zones = zones

        card = tk.Frame(self, bg="#FFFFFF", padx=20, pady=20, bd=1, relief="solid")
        card.config(highlightbackground=THEME["border"])
        card.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(card, text="Add New Parking Slot", font=(THEME["font_family"], 12, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 15))

        # Slot Code
        tk.Label(card, text="Slot Identifier Code (e.g., A-15):", bg="#FFFFFF", font=(THEME["font_family"], 9)).pack(anchor="w")
        self.ent_code = ttk.Entry(card)
        self.ent_code.pack(fill="x", pady=(2, 10))

        # Zone
        tk.Label(card, text="Parking Zone:", bg="#FFFFFF", font=(THEME["font_family"], 9)).pack(anchor="w")
        zone_names = [f"{z.code} — {z.name}" for z in self.zones]
        self.cb_zone = ttk.Combobox(card, values=zone_names, state="readonly")
        if zone_names:
            self.cb_zone.current(0)
        self.cb_zone.pack(fill="x", pady=(2, 10))

        # Category
        tk.Label(card, text="Supported Vehicle Category:", bg="#FFFFFF", font=(THEME["font_family"], 9)).pack(anchor="w")
        categories = ["CAR", "TWO_WHEELER", "SUV", "COMMERCIAL", "EV"]
        self.cb_cat = ttk.Combobox(card, values=categories, state="readonly")
        self.cb_cat.current(0)
        self.cb_cat.pack(fill="x", pady=(2, 15))

        # Actions
        btn_frame = tk.Frame(card, bg="#FFFFFF")
        btn_frame.pack(fill="x", pady=(5, 0))

        btn_save = ttk.Button(btn_frame, text="Add Slot", style="Primary.TButton", command=self._save)
        btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_cancel = ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy)
        btn_cancel.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _save(self):
        code = self.ent_code.get().strip().upper()
        if not code:
            messagebox.showerror("Validation Error", "Slot code cannot be empty.")
            return

        sel_idx = self.cb_zone.current()
        if sel_idx < 0 or sel_idx >= len(self.zones):
            messagebox.showerror("Validation Error", "Please select a valid zone.")
            return

        zone_id = self.zones[sel_idx].id
        cat = self.cb_cat.get()

        self.on_slot_added(code, zone_id, cat, self)
