"""
ParkSmart Pro — Paginated Table Component with Sorting and Treeview
TQM Quality Attribute: Usability & Performance Efficiency
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Callable, Optional
from config import THEME

class PaginatedTable(tk.Frame):
    def __init__(self, parent, columns: List[Dict[str, Any]], on_page_change: Optional[Callable] = None,
                 on_row_double_click: Optional[Callable] = None, **kwargs):
        """
        columns: [{"id": "ticket_no", "text": "Ticket #", "width": 120, "anchor": "w"}, ...]
        """
        super().__init__(parent, bg=THEME["bg_card"], bd=1, relief="solid",
                         highlightthickness=0, **kwargs)
        self.config(highlightbackground=THEME["border"])
        self.columns_def = columns
        self.on_page_change = on_page_change
        self.on_row_double_click = on_row_double_click

        self.current_page = 1
        self.page_size = 25
        self.total_records = 0
        self.sort_col = None
        self.sort_desc = False

        # Table container
        table_frame = tk.Frame(self, bg=THEME["bg_card"])
        table_frame.pack(fill="both", expand=True)

        col_ids = [c["id"] for c in columns]
        self.tree = ttk.Treeview(
            table_frame,
            columns=col_ids,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse"
        )

        for col in columns:
            cid = col["id"]
            ctext = col["text"]
            cwidth = col.get("width", 100)
            canchor = col.get("anchor", "w")
            self.tree.heading(cid, text=ctext, anchor=canchor, command=lambda c=cid: self._handle_sort(c))
            self.tree.column(cid, width=cwidth, minwidth=60, anchor=canchor)

        # Scrollbar
        sb_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb_y.pack(side="right", fill="y")

        # Double click event
        if self.on_row_double_click:
            self.tree.bind("<Double-1>", self._on_double_click)

        # Pagination Bar
        self.p_bar = tk.Frame(self, bg="#F8FAFC", height=38, padx=10, pady=4)
        self.p_bar.pack(fill="x", side="bottom")

        # Left Info
        self.lbl_info = tk.Label(
            self.p_bar, text="Showing 0 of 0 records",
            bg="#F8FAFC", fg=THEME["text_muted"], font=(THEME["font_family"], 8)
        )
        self.lbl_info.pack(side="left")

        # Right Controls
        ctrl_frame = tk.Frame(self.p_bar, bg="#F8FAFC")
        ctrl_frame.pack(side="right")

        self.btn_first = tk.Button(ctrl_frame, text="«", width=2, command=self._go_first, relief="flat", bg="#FFFFFF", bd=1)
        self.btn_first.pack(side="left", padx=2)

        self.btn_prev = tk.Button(ctrl_frame, text="‹", width=2, command=self._go_prev, relief="flat", bg="#FFFFFF", bd=1)
        self.btn_prev.pack(side="left", padx=2)

        self.lbl_page = tk.Label(ctrl_frame, text="Page 1 of 1", bg="#F8FAFC", font=(THEME["font_family"], 8))
        self.lbl_page.pack(side="left", padx=6)

        self.btn_next = tk.Button(ctrl_frame, text="›", width=2, command=self._go_next, relief="flat", bg="#FFFFFF", bd=1)
        self.btn_next.pack(side="left", padx=2)

        self.btn_last = tk.Button(ctrl_frame, text="»", width=2, command=self._go_last, relief="flat", bg="#FFFFFF", bd=1)
        self.btn_last.pack(side="left", padx=2)

    def _on_double_click(self, event):
        item_id = self.tree.focus()
        if item_id and self.on_row_double_click:
            vals = self.tree.item(item_id, "values")
            self.on_row_double_click(vals)

    def _handle_sort(self, col_id: str):
        if self.sort_col == col_id:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_col = col_id
            self.sort_desc = False
        # Update column header indicator
        for col in self.columns_def:
            cid = col["id"]
            text = col["text"]
            if cid == self.sort_col:
                arrow = " ▼" if self.sort_desc else " ▲"
                self.tree.heading(cid, text=text + arrow)
            else:
                self.tree.heading(cid, text=text)

        if self.on_page_change:
            self.on_page_change(self.current_page, self.page_size, self.sort_col, self.sort_desc)

    def set_data(self, rows: List[List[Any]], total_count: int, current_page: int = 1, page_size: int = 25):
        """Populate treeview with row data."""
        self.current_page = current_page
        self.page_size = page_size
        self.total_records = total_count

        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new rows with alternating colors
        self.tree.tag_configure("even", background="#FFFFFF")
        self.tree.tag_configure("odd", background="#F8FAFC")

        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end", values=row, tags=(tag,))

        # Update Pagination Info
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        start_idx = (current_page - 1) * page_size + 1 if total_count > 0 else 0
        end_idx = min(total_count, current_page * page_size)

        self.lbl_info.config(text=f"Showing {start_idx}-{end_idx} of {total_count:,} records")
        self.lbl_page.config(text=f"Page {current_page} of {total_pages}")

        self.btn_first.config(state="normal" if current_page > 1 else "disabled")
        self.btn_prev.config(state="normal" if current_page > 1 else "disabled")
        self.btn_next.config(state="normal" if current_page < total_pages else "disabled")
        self.btn_last.config(state="normal" if current_page < total_pages else "disabled")

    def _go_first(self):
        if self.current_page > 1:
            self._trigger_page(1)

    def _go_prev(self):
        if self.current_page > 1:
            self._trigger_page(self.current_page - 1)

    def _go_next(self):
        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self._trigger_page(self.current_page + 1)

    def _go_last(self):
        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self._trigger_page(total_pages)

    def _trigger_page(self, page_num: int):
        self.current_page = page_num
        if self.on_page_change:
            self.on_page_change(self.current_page, self.page_size, self.sort_col, self.sort_desc)
