"""
ParkSmart Pro — Data Formatting Utilities
Consistent UI presentation and financial calculation safety.
"""

from datetime import datetime, timedelta
from typing import Union, Optional
from config import CURRENCY_SYMBOL, CURRENCY_FACTOR, THEME

def format_currency(minor_units: Optional[int]) -> str:
    """Format minor currency units (cents/paise) to display string (e.g., 2550 -> '$25.50')."""
    if minor_units is None:
        return f"{CURRENCY_SYMBOL}0.00"
    val = minor_units / CURRENCY_FACTOR
    return f"{CURRENCY_SYMBOL}{val:,.2f}"

def format_duration(total_minutes: Union[int, float]) -> str:
    """Format duration in minutes into a human-readable string like '2h 15m' or '45m'."""
    if total_minutes is None or total_minutes < 0:
        return "0m"
    total_minutes = int(round(total_minutes))
    days = total_minutes // 1440
    remaining = total_minutes % 1440
    hours = remaining // 60
    mins = remaining % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    return " ".join(parts)

def format_datetime(dt: Union[str, datetime, None], fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime consistently across UI."""
    if not dt:
        return "-"
    if isinstance(dt, str):
        try:
            # Handle ISO formats
            clean_str = dt.replace("T", " ")
            if "." in clean_str:
                clean_str = clean_str.split(".")[0]
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return str(dt)
    return dt.strftime(fmt)

def get_status_style(status: str) -> dict:
    """Get theme colors and labels for status badges."""
    status_upper = (status or "").upper()
    styles = {
        "AVAILABLE": {"bg": "#DCFCE7", "fg": "#166534", "label": "AVAILABLE", "icon": "●"},
        "OCCUPIED": {"bg": "#FEE2E2", "fg": "#991B1B", "label": "OCCUPIED", "icon": "■"},
        "RESERVED": {"bg": "#FEF3C7", "fg": "#92400E", "label": "RESERVED", "icon": "▲"},
        "MAINTENANCE": {"bg": "#F1F5F9", "fg": "#475569", "label": "MAINTENANCE", "icon": "✖"},
        "OUT_OF_SERVICE": {"bg": "#F1F5F9", "fg": "#475569", "label": "OUT OF SERVICE", "icon": "✖"},
        "ACTIVE": {"bg": "#DBEAFE", "fg": "#1E40AF", "label": "ACTIVE", "icon": "▶"},
        "COMPLETED": {"bg": "#DCFCE7", "fg": "#166534", "label": "COMPLETED", "icon": "✔"},
        "CANCELLED": {"bg": "#FEE2E2", "fg": "#991B1B", "label": "CANCELLED", "icon": "✖"},
        "EXPIRED": {"bg": "#F3F4F6", "fg": "#6B7280", "label": "EXPIRED", "icon": "⏳"},
        "CONFIRMED": {"bg": "#EDE9FE", "fg": "#5B21B6", "label": "CONFIRMED", "icon": "★"},
        "PAID": {"bg": "#DCFCE7", "fg": "#166534", "label": "PAID", "icon": "✔"},
        "UNPAID": {"bg": "#FEE2E2", "fg": "#991B1B", "label": "UNPAID", "icon": "!"},
    }
    return styles.get(status_upper, {"bg": "#F1F5F9", "fg": "#334155", "label": status_upper, "icon": "•"})
