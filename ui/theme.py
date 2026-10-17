"""
ParkSmart Pro — Modern Desktop UI Styling & Theme System
TQM Quality Attribute: Usability & User Interface Aesthetics (ISO/IEC 25010)
"""

import tkinter as tk
from tkinter import ttk
from config import THEME

def setup_styles(root: tk.Tk):
    """Initialize consistent ttk styles, fonts, and widget appearances."""
    style = ttk.Style(root)
    # Use clam or default theme for reliable custom background/foreground styling on Windows
    try:
        style.theme_use("clam")
    except Exception:
        pass

    font_family = THEME["font_family"]

    # Configure Base Frame Styles
    style.configure("Main.TFrame", background=THEME["bg_main"])
    style.configure("Card.TFrame", background=THEME["bg_card"], relief="flat")
    style.configure("Sidebar.TFrame", background=THEME["bg_sidebar"])
    style.configure("Header.TFrame", background=THEME["bg_header"], relief="flat")

    # Configure Label Styles
    style.configure("TLabel", background=THEME["bg_card"], foreground=THEME["text_dark"], font=(font_family, 10))
    style.configure("HeaderTitle.TLabel", background=THEME["bg_header"], foreground=THEME["text_dark"], font=(font_family, 14, "bold"))
    style.configure("HeaderSub.TLabel", background=THEME["bg_header"], foreground=THEME["text_muted"], font=(font_family, 9))
    style.configure("CardTitle.TLabel", background=THEME["bg_card"], foreground=THEME["text_muted"], font=(font_family, 9, "bold"))
    style.configure("CardValue.TLabel", background=THEME["bg_card"], foreground=THEME["text_dark"], font=(font_family, 20, "bold"))
    style.configure("CardSub.TLabel", background=THEME["bg_card"], foreground=THEME["text_muted"], font=(font_family, 8))
    style.configure("SectionTitle.TLabel", background=THEME["bg_main"], foreground=THEME["text_dark"], font=(font_family, 12, "bold"))

    # Configure Button Styles
    style.configure(
        "Primary.TButton",
        background=THEME["primary"],
        foreground="#FFFFFF",
        font=(font_family, 10, "bold"),
        borderwidth=0,
        focuscolor="none",
        padding=(12, 6)
    )
    style.map(
        "Primary.TButton",
        background=[("active", THEME["primary_hover"]), ("disabled", THEME["neutral"])],
        foreground=[("disabled", "#F1F5F9")]
    )

    style.configure(
        "Success.TButton",
        background=THEME["success"],
        foreground="#FFFFFF",
        font=(font_family, 10, "bold"),
        borderwidth=0,
        focuscolor="none",
        padding=(12, 6)
    )
    style.map(
        "Success.TButton",
        background=[("active", "#059669"), ("disabled", THEME["neutral"])],
        foreground=[("disabled", "#F1F5F9")]
    )

    style.configure(
        "Danger.TButton",
        background=THEME["danger"],
        foreground="#FFFFFF",
        font=(font_family, 10, "bold"),
        borderwidth=0,
        focuscolor="none",
        padding=(12, 6)
    )

    style.configure(
        "Secondary.TButton",
        background="#E2E8F0",
        foreground=THEME["text_dark"],
        font=(font_family, 10),
        borderwidth=0,
        focuscolor="none",
        padding=(10, 5)
    )
    style.map(
        "Secondary.TButton",
        background=[("active", "#CBD5E1")]
    )

    # Configure Treeview (Data Tables)
    style.configure(
        "Custom.Treeview",
        background="#FFFFFF",
        foreground=THEME["text_dark"],
        rowheight=28,
        fieldbackground="#FFFFFF",
        font=(font_family, 9),
        borderwidth=0
    )
    style.configure(
        "Custom.Treeview.Heading",
        background="#F8FAFC",
        foreground=THEME["text_dark"],
        font=(font_family, 9, "bold"),
        borderwidth=1,
        relief="flat"
    )
    style.map("Custom.Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", "#1E40AF")])

    # Configure Entry and Combobox
    style.configure("TEntry", fieldbackground="#FFFFFF", foreground=THEME["text_dark"], padding=5)
    style.configure("TCombobox", fieldbackground="#FFFFFF", padding=5)
