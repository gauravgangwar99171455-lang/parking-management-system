"""
ParkSmart Pro — Parking Tariff Configuration View
TQM Quality Attribute: Maintainability & Policy Configuration
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME, CURRENCY_SYMBOL
from services.billing_service import billing_service
from utils.formatters import format_currency
from utils.validators import validate_positive_amount

class TariffsView(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.on_navigate = on_navigate

        self.content_frame = tk.Frame(self, bg=THEME["bg_main"], padx=25, pady=20)
        self.content_frame.pack(fill="both", expand=True)

        self._build_header()
        self._build_table_and_editor()

    def _build_header(self):
        bar = tk.Frame(self.content_frame, bg="#FFFFFF", padx=18, pady=14, bd=1, relief="solid")
        bar.config(highlightbackground=THEME["border"], highlightthickness=0)
        bar.pack(fill="x", pady=(0, 15))

        tk.Label(
            bar, text="💲 Parking Tariff Management",
            font=(THEME["font_family"], 13, "bold"), bg="#FFFFFF", fg=THEME["text_dark"]
        ).pack(side="left")

        tk.Label(
            bar, text="TQM Notice: Modifying tariffs applies strictly to future sessions. Historical bills remain immutable.",
            font=(THEME["font_family"], 8, "italic"), bg="#FFFFFF", fg=THEME["text_muted"]
        ).pack(side="right")

    def _build_table_and_editor(self):
        split = tk.Frame(self.content_frame, bg=THEME["bg_main"])
        split.pack(fill="both", expand=True)

        # Left Table of Current Tariffs
        left = tk.Frame(split, bg="#FFFFFF", padx=15, pady=15, bd=1, relief="solid")
        left.config(highlightbackground=THEME["border"], highlightthickness=0)
        left.pack(side="left", fill="both", expand=True, padx=(0, 15))

        cols = ("id", "cat", "base_dur", "base_rate", "hourly", "max_day", "grace", "lost")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", style="Custom.Treeview")
        self.tree.heading("id", text="ID")
        self.tree.heading("cat", text="Vehicle Category", anchor="w")
        self.tree.heading("base_dur", text="Base Min", anchor="center")
        self.tree.heading("base_rate", text="Base Rate", anchor="e")
        self.tree.heading("hourly", text="Hourly Rate", anchor="e")
        self.tree.heading("max_day", text="Daily Cap", anchor="e")
        self.tree.heading("grace", text="Grace (m)", anchor="center")
        self.tree.heading("lost", text="Lost Tkt Fee", anchor="e")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("cat", width=120)
        self.tree.column("base_dur", width=70, anchor="center")
        self.tree.column("base_rate", width=80, anchor="e")
        self.tree.column("hourly", width=80, anchor="e")
        self.tree.column("max_day", width=80, anchor="e")
        self.tree.column("grace", width=65, anchor="center")
        self.tree.column("lost", width=80, anchor="e")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_tariff)

        # Right Form Editor
        self.editor = tk.Frame(split, bg="#FFFFFF", padx=20, pady=18, bd=1, relief="solid", width=300)
        self.editor.config(highlightbackground=THEME["border"], highlightthickness=0)
        self.editor.pack(side="right", fill="y")
        self.editor.pack_propagate(False)

        tk.Label(self.editor, text="Edit Selected Tariff", font=(THEME["font_family"], 11, "bold"),
                 bg="#FFFFFF", fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 12))

        self.lbl_selected_cat = tk.Label(self.editor, text="Select a category from table",
                                         font=(THEME["font_family"], 9, "bold"), bg="#FFFFFF", fg=THEME["primary"])
        self.lbl_selected_cat.pack(anchor="w", pady=(0, 10))

        # Fields
        self.selected_tariff_id = None

        tk.Label(self.editor, text="Base Duration (Minutes):", font=(THEME["font_family"], 8, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_base_dur = ttk.Entry(self.editor)
        self.ent_base_dur.pack(fill="x", pady=(2, 6))

        tk.Label(self.editor, text=f"Base Rate ({CURRENCY_SYMBOL}):", font=(THEME["font_family"], 8, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_base_rate = ttk.Entry(self.editor)
        self.ent_base_rate.pack(fill="x", pady=(2, 6))

        tk.Label(self.editor, text=f"Hourly Rate ({CURRENCY_SYMBOL}):", font=(THEME["font_family"], 8, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_hourly = ttk.Entry(self.editor)
        self.ent_hourly.pack(fill="x", pady=(2, 6))

        tk.Label(self.editor, text=f"Daily Maximum Cap ({CURRENCY_SYMBOL}):", font=(THEME["font_family"], 8, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_max = ttk.Entry(self.editor)
        self.ent_max.pack(fill="x", pady=(2, 6))

        tk.Label(self.editor, text="Grace Period (Minutes):", font=(THEME["font_family"], 8, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_grace = ttk.Entry(self.editor)
        self.ent_grace.pack(fill="x", pady=(2, 6))

        tk.Label(self.editor, text=f"Lost Ticket Penalty ({CURRENCY_SYMBOL}):", font=(THEME["font_family"], 8, "bold"), bg="#FFFFFF").pack(anchor="w")
        self.ent_lost = ttk.Entry(self.editor)
        self.ent_lost.pack(fill="x", pady=(2, 14))

        self.btn_save = ttk.Button(self.editor, text="Save Tariff Changes", style="Primary.TButton",
                                   command=self._save_tariff, state="disabled")
        self.btn_save.pack(fill="x")

    def refresh_tariffs(self):
        tariffs = billing_service.get_all_tariffs()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for t in tariffs:
            self.tree.insert("", "end", values=(
                t.id,
                t.vehicle_category,
                t.base_duration_minutes,
                format_currency(t.base_rate_cents),
                format_currency(t.hourly_rate_cents),
                format_currency(t.daily_max_cents),
                t.grace_period_minutes,
                format_currency(t.lost_ticket_fee_cents)
            ))

    def _on_select_tariff(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        tid, cat, bdur, brate, hrly, maxd, grace, lost = vals

        self.selected_tariff_id = int(tid)
        self.lbl_selected_cat.config(text=f"Editing: {cat}")

        self.ent_base_dur.delete(0, tk.END)
        self.ent_base_dur.insert(0, str(bdur))

        self.ent_base_rate.delete(0, tk.END)
        self.ent_base_rate.insert(0, brate.replace(CURRENCY_SYMBOL, ""))

        self.ent_hourly.delete(0, tk.END)
        self.ent_hourly.insert(0, hrly.replace(CURRENCY_SYMBOL, ""))

        self.ent_max.delete(0, tk.END)
        self.ent_max.insert(0, maxd.replace(CURRENCY_SYMBOL, ""))

        self.ent_grace.delete(0, tk.END)
        self.ent_grace.insert(0, str(grace))

        self.ent_lost.delete(0, tk.END)
        self.ent_lost.insert(0, lost.replace(CURRENCY_SYMBOL, ""))

        self.btn_save.config(state="normal")

    def _save_tariff(self):
        if not self.selected_tariff_id:
            return

        try:
            bdur = int(self.ent_base_dur.get().strip())
            grace = int(self.ent_grace.get().strip())
            ok1, brate_c, m1 = validate_positive_amount(self.ent_base_rate.get())
            ok2, hrly_c, m2 = validate_positive_amount(self.ent_hourly.get())
            ok3, max_c, m3 = validate_positive_amount(self.ent_max.get())
            ok4, lost_c, m4 = validate_positive_amount(self.ent_lost.get())

            if not (ok1 and ok2 and ok3 and ok4):
                messagebox.showerror("Validation Error", "All monetary values must be valid positive numbers.")
                return

            ok, msg = billing_service.update_tariff(
                tariff_id=self.selected_tariff_id,
                base_duration_mins=bdur,
                base_rate_cents=brate_c,
                hourly_rate_cents=hrly_c,
                daily_max_cents=max_c,
                grace_mins=grace,
                lost_fee_cents=lost_c
            )

            if ok:
                messagebox.showinfo("Success", msg)
                self.refresh_tariffs()
            else:
                messagebox.showerror("Error", msg)

        except ValueError:
            messagebox.showerror("Validation Error", "Please verify duration and grace period are integer numbers.")
