"""
ParkSmart Pro — Vehicle Exit & Automated Billing View
TQM Quality Attribute: Financial Accuracy, Transparency & Transaction Atomicity
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from config import THEME
from services.billing_service import billing_service, AUTHORIZED_DISCOUNTS
from services.auth_service import auth_service
from ui.components.dialogs import ReceiptDialog
from utils.formatters import format_currency

class VehicleExitView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.active_session = None

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=25, pady=20)
        self.content_frame.pack(fill="both", expand=True)

        # 1. Search Bar Top Card
        self._build_search_card()

        # 2. Main Content Split: Session Details (Left) + Billing Summary & Payment (Right)
        self.split_frame = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        self.split_frame.pack(fill="both", expand=True, pady=(15, 0))

        self._build_session_card()
        self._build_payment_card()

    def _build_search_card(self):
        card = tk.Frame(self.content_frame, bg="#FFFFFF", padx=20, pady=16, bd=1, relief="solid")
        card.config(highlightbackground=THEME["border"], highlightthickness=0)
        card.pack(fill="x")

        tk.Label(
            card, text="📤 Vehicle Checkout & Settlement",
            font=(THEME["font_family"], 13, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]
        ).pack(side="left", padx=(0, 20))

        # Search Input
        tk.Label(card, text="Scan Ticket # or Plate:", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(side="left", padx=(0, 6))

        self.ent_search = ttk.Entry(card, width=24, font=("Consolas", 11, "bold"))
        self.ent_search.pack(side="left", padx=(0, 10))
        self.ent_search.bind("<Return>", lambda e: self._lookup_session())

        btn_find = ttk.Button(card, text="🔍 Look Up Active Session", style="Primary.TButton", command=self._lookup_session)
        btn_find.pack(side="left", padx=(0, 15))

        btn_clear = ttk.Button(card, text="Clear", style="Secondary.TButton", command=self._clear_view)
        btn_clear.pack(side="left")

    def _build_session_card(self):
        self.card_session = tk.Frame(self.split_frame, bg="#FFFFFF", padx=20, pady=18, bd=1, relief="solid")
        self.card_session.config(highlightbackground=THEME["border"], highlightthickness=0)
        self.card_session.pack(side="left", fill="both", expand=True, padx=(0, 15))

        tk.Label(
            self.card_session, text="Parking Session Details",
            font=(THEME["font_family"], 11, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]
        ).pack(anchor="w", pady=(0, 12))

        # Details Grid
        self.detail_labels = {}
        fields = [
            ("ticket_no", "Ticket Number:"),
            ("vehicle_reg", "Registration:"),
            ("category", "Category:"),
            ("slot", "Allocated Bay:"),
            ("entry_time", "Entry Time:"),
            ("duration", "Elapsed Duration:"),
            ("tariff_info", "Tariff Rules:"),
        ]

        grid = tk.Frame(self.card_session, bg="#FFFFFF")
        grid.pack(fill="x", pady=5)

        for i, (k, label_text) in enumerate(fields):
            tk.Label(grid, text=label_text, font=(THEME["font_family"], 9, "bold"),
                     bg="#FFFFFF", fg=THEME["text_muted"], anchor="w").grid(row=i, column=0, sticky="w", pady=5)

            val_lbl = tk.Label(grid, text="-", font=(THEME["font_family"], 9),
                               bg="#FFFFFF", fg=THEME["text_dark"], anchor="w")
            val_lbl.grid(row=i, column=1, sticky="w", pady=5, padx=(10, 0))
            self.detail_labels[k] = val_lbl

        grid.columnconfigure(1, weight=1)

        self.lbl_no_session = tk.Label(
            self.card_session, text="Scan a ticket or enter vehicle registration above to begin checkout.",
            font=(THEME["font_family"], 9), bg="#FFFFFF", fg=THEME["text_muted"]
        )
        self.lbl_no_session.pack(pady=30)

    def _build_payment_card(self):
        self.card_payment = tk.Frame(self.split_frame, bg="#FFFFFF", padx=20, pady=18, bd=1, relief="solid")
        self.card_payment.config(highlightbackground=THEME["border"], highlightthickness=0)
        self.card_payment.pack(side="right", fill="both", expand=True)

        tk.Label(
            self.card_payment, text="Financial Calculation & Settlement",
            font=(THEME["font_family"], 11, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]
        ).pack(anchor="w", pady=(0, 12))

        # Financial Breakdown Rows
        fin_frame = tk.Frame(self.card_payment, bg="#F8FAFC", padx=15, pady=12, bd=1, relief="solid")
        fin_frame.config(highlightbackground=THEME["border"], highlightthickness=0)
        fin_frame.pack(fill="x", pady=(0, 15))

        # Gross
        f_row1 = tk.Frame(fin_frame, bg="#F8FAFC")
        f_row1.pack(fill="x", pady=2)
        tk.Label(f_row1, text="Gross Parking Fee:", bg="#F8FAFC", font=(THEME["font_family"], 9)).pack(side="left")
        self.lbl_gross = tk.Label(f_row1, text="$0.00", bg="#F8FAFC", font=(THEME["font_family"], 9, "bold"))
        self.lbl_gross.pack(side="right")

        # Discount Selection
        f_row2 = tk.Frame(fin_frame, bg="#F8FAFC")
        f_row2.pack(fill="x", pady=6)
        tk.Label(f_row2, text="Authorized Discount:", bg="#F8FAFC", font=(THEME["font_family"], 9)).pack(side="left")

        disc_names = [f"{k} — {v['name']}" for k, v in AUTHORIZED_DISCOUNTS.items()]
        self.cb_discount = ttk.Combobox(f_row2, values=disc_names, state="readonly", width=22)
        self.cb_discount.current(0)
        self.cb_discount.pack(side="right")
        self.cb_discount.bind("<<ComboboxSelected>>", lambda e: self._recalc_bill())

        # Net Payable Highlight
        tk.Frame(fin_frame, bg=THEME["border"], height=1).pack(fill="x", pady=6)
        f_row3 = tk.Frame(fin_frame, bg="#F8FAFC")
        f_row3.pack(fill="x", pady=4)
        tk.Label(f_row3, text="TOTAL PAYABLE:", bg="#F8FAFC", font=(THEME["font_family"], 11, "bold"),
                 fg=THEME["text_dark"]).pack(side="left")
        self.lbl_net = tk.Label(f_row3, text="$0.00", bg="#F8FAFC", font=(THEME["font_family"], 14, "bold"),
                                fg=THEME["success"])
        self.lbl_net.pack(side="right")

        # Payment Mode Dropdown
        tk.Label(self.card_payment, text="Payment Method *", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(10, 2))

        self.cb_pay_mode = ttk.Combobox(
            self.card_payment,
            values=["CASH", "CARD", "UPI", "WALLET", "WAIVED"],
            state="readonly", font=(THEME["font_family"], 10)
        )
        self.cb_pay_mode.current(0)
        self.cb_pay_mode.pack(fill="x", pady=(0, 15))

        # Remarks
        tk.Label(self.card_payment, text="Cashier Remarks (Optional)", font=(THEME["font_family"], 9, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 2))
        self.ent_remarks = ttk.Entry(self.card_payment)
        self.ent_remarks.pack(fill="x", pady=(0, 18))

        # Settlement Action Button
        self.btn_pay = ttk.Button(
            self.card_payment, text="Settle Payment & Release Slot ➔",
            style="Success.TButton",
            state="disabled",
            command=self._process_payment,
            cursor="hand2"
        )
        self.btn_pay.pack(fill="x", ipady=4)

    def _lookup_session(self):
        query = self.ent_search.get().strip()
        if not query:
            messagebox.showwarning("Search", "Please enter a ticket number or vehicle registration plate.")
            return

        session = billing_service.find_active_session(query)
        if not session:
            messagebox.showerror("Not Found", f"No active parking session found for '{query}'.\nCheck ticket number or vehicle plate.")
            self._clear_view()
            return

        self.active_session = session
        self.lbl_no_session.pack_forget()

        # Update Session Details Card
        self.detail_labels["ticket_no"].config(text=session.ticket_number, font=("Consolas", 10, "bold"))
        self.detail_labels["vehicle_reg"].config(text=session.vehicle_registration, font=("Consolas", 10, "bold"))
        self.detail_labels["category"].config(text=session.vehicle_category)
        self.detail_labels["slot"].config(text=f"{session.slot_code} ({session.zone_name or 'General'})")
        self.detail_labels["entry_time"].config(text=session.entry_time)

        self._recalc_bill()
        self.btn_pay.config(state="normal")

    def _get_selected_discount_code(self) -> str:
        val = self.cb_discount.get()
        return val.split(" — ")[0] if val else "NONE"

    def _recalc_bill(self):
        if not self.active_session:
            return
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        disc_code = self._get_selected_discount_code()

        bill = billing_service.calculate_bill(
            entry_time_str=self.active_session.entry_time,
            exit_time_str=now_iso,
            category=self.active_session.vehicle_category,
            discount_code=disc_code
        )

        self.current_bill = bill
        self.detail_labels["duration"].config(text=f"{bill['duration_formatted']} ({bill['duration_minutes']} mins)")
        t = bill["tariff"]
        self.detail_labels["tariff_info"].config(
            text=f"Base: {format_currency(t.base_rate_cents)} ({t.base_duration_minutes}m) | Extra: {format_currency(t.hourly_rate_cents)}/h"
        )

        self.lbl_gross.config(text=format_currency(bill["gross_cents"]))
        self.lbl_net.config(text=format_currency(bill["net_cents"]))

    def _process_payment(self):
        if not self.active_session:
            return

        method = self.cb_pay_mode.get()
        disc_code = self._get_selected_discount_code()
        remarks = self.ent_remarks.get().strip()
        user = auth_service.current_user
        uid = user.id if user else None
        uname = user.username if user else None

        ok, receipt, msg = billing_service.process_exit_and_payment(
            session_id=self.active_session.id,
            payment_method=method,
            discount_code=disc_code,
            cashier_id=uid,
            cashier_name=uname,
            notes=remarks
        )

        if ok and receipt:
            ReceiptDialog(self, receipt)
            self._clear_view()
        else:
            messagebox.showerror("Checkout Failed", msg)

    def _clear_view(self):
        self.active_session = None
        self.ent_search.delete(0, tk.END)
        self.ent_remarks.delete(0, tk.END)
        for lbl in self.detail_labels.values():
            lbl.config(text="-")
        self.lbl_gross.config(text="$0.00")
        self.lbl_net.config(text="$0.00")
        self.cb_discount.current(0)
        self.cb_pay_mode.current(0)
        self.btn_pay.config(state="disabled")
        self.lbl_no_session.pack(pady=30)
