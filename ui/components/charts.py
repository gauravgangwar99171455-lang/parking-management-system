"""
ParkSmart Pro — Dynamic Vector Charts & Visualizations
Native Tkinter Canvas Rendering with High-DPI Precision + Matplotlib Adapter
TQM Quality Attribute: Environmental Robustness & Performance Efficiency
"""

import math
import tkinter as tk
from typing import Dict, List, Tuple
from config import THEME

class DonutChart(tk.Canvas):
    def __init__(self, parent, width: int = 260, height: int = 240, **kwargs):
        super().__init__(parent, width=width, height=height, bg=THEME["bg_card"],
                         bd=0, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height

    def draw(self, slices: List[Tuple[str, float, str]], center_text: str = "", center_sub: str = ""):
        """
        Draw a donut chart.
        slices: [(label, value, hex_color), ...]
        """
        self.delete("all")
        total = sum(v for _, v, _ in slices)
        if total <= 0:
            self.create_text(self.width // 2, self.height // 2, text="No Data Available",
                             fill=THEME["text_muted"], font=(THEME["font_family"], 10))
            return

        cx = self.width // 2
        cy = (self.height // 2) - 15
        radius = min(cx, cy) - 20
        inner_radius = int(radius * 0.62)

        start_angle = 90.0

        # Draw outer segments
        for label, val, color in slices:
            if val <= 0:
                continue
            extent = (val / total) * 360.0
            self.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=start_angle, extent=extent, fill=color, outline=THEME["bg_card"], width=2
            )
            start_angle += extent

        # Draw inner cutout
        self.create_oval(
            cx - inner_radius, cy - inner_radius, cx + inner_radius, cy + inner_radius,
            fill=THEME["bg_card"], outline=THEME["bg_card"]
        )

        # Center Text
        if center_text:
            self.create_text(
                cx, cy - 6, text=center_text,
                fill=THEME["text_dark"], font=(THEME["font_family"], 14, "bold")
            )
        if center_sub:
            self.create_text(
                cx, cy + 12, text=center_sub,
                fill=THEME["text_muted"], font=(THEME["font_family"], 8)
            )

        # Bottom Legend
        legend_y = self.height - 25
        num_items = len([s for s in slices if s[1] > 0])
        if num_items > 0:
            spacing = self.width / max(1, num_items)
            cur_x = spacing / 2
            for label, val, color in slices:
                if val <= 0:
                    continue
                # Color dot
                self.create_oval(cur_x - 16, legend_y - 4, cur_x - 8, legend_y + 4, fill=color, outline="")
                # Label + count
                pct = int(round((val / total) * 100))
                self.create_text(
                    cur_x + 12, legend_y,
                    text=f"{label} ({pct}%)",
                    fill=THEME["text_muted"], font=(THEME["font_family"], 7, "bold")
                )
                cur_x += spacing

class BarChart(tk.Canvas):
    def __init__(self, parent, width: int = 380, height: int = 240, **kwargs):
        super().__init__(parent, width=width, height=height, bg=THEME["bg_card"],
                         bd=0, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height

    def draw(self, categories: List[str], values: List[float], color: str = "#2563EB", unit: str = ""):
        """Draw clean modern vertical bar chart."""
        self.delete("all")
        if not values or max(values) == 0:
            self.create_text(self.width // 2, self.height // 2, text="No Data Available",
                             fill=THEME["text_muted"], font=(THEME["font_family"], 10))
            return

        padding_left = 40
        padding_right = 20
        padding_top = 25
        padding_bottom = 35

        plot_w = self.width - padding_left - padding_right
        plot_h = self.height - padding_top - padding_bottom

        max_val = max(values)
        num_bars = len(values)
        bar_width = min(40, max(14, int((plot_w / max(1, num_bars)) * 0.65)))
        spacing = plot_w / max(1, num_bars)

        # Baseline Axis
        self.create_line(
            padding_left, self.height - padding_bottom,
            self.width - padding_right, self.height - padding_bottom,
            fill=THEME["border"], width=1
        )

        for i, (cat, val) in enumerate(zip(categories, values)):
            bx = padding_left + (i * spacing) + (spacing - bar_width) / 2
            h_ratio = val / max_val if max_val > 0 else 0
            bh = int(h_ratio * plot_h)
            by = self.height - padding_bottom - bh

            # Bar with rounded top
            self.create_rectangle(
                bx, by, bx + bar_width, self.height - padding_bottom,
                fill=color, outline=""
            )

            # Value label on top
            val_text = f"{int(val)}" if val == int(val) else f"{val:.1f}"
            self.create_text(
                bx + bar_width / 2, by - 8,
                text=f"{val_text}{unit}",
                fill=THEME["text_dark"], font=(THEME["font_family"], 7, "bold")
            )

            # Category label below
            short_cat = cat[:6] + ".." if len(cat) > 7 else cat
            self.create_text(
                bx + bar_width / 2, self.height - padding_bottom + 12,
                text=short_cat,
                fill=THEME["text_muted"], font=(THEME["font_family"], 7)
            )

class LineTrendChart(tk.Canvas):
    def __init__(self, parent, width: int = 380, height: int = 240, **kwargs):
        super().__init__(parent, width=width, height=height, bg=THEME["bg_card"],
                         bd=0, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height

    def draw(self, x_labels: List[str], y_values: List[float], color: str = "#10B981", prefix: str = "$"):
        """Draw filled line trend chart."""
        self.delete("all")
        if not y_values:
            self.create_text(self.width // 2, self.height // 2, text="No Historical Data",
                             fill=THEME["text_muted"], font=(THEME["font_family"], 10))
            return

        pad_l = 45
        pad_r = 25
        pad_t = 25
        pad_b = 35

        plot_w = self.width - pad_l - pad_r
        plot_h = self.height - pad_t - pad_b

        max_val = max(y_values)
        if max_val == 0:
            max_val = 1.0

        n = len(y_values)
        step_x = plot_w / max(1, n - 1) if n > 1 else plot_w

        # Draw grid lines
        for step in (0.25, 0.5, 0.75, 1.0):
            gy = pad_t + plot_h - int(step * plot_h)
            self.create_line(pad_l, gy, self.width - pad_r, gy, fill="#F1F5F9", width=1)

        points = []
        for i, val in enumerate(y_values):
            px = pad_l + (i * step_x)
            py = pad_t + plot_h - int((val / max_val) * plot_h)
            points.append((px, py))

        # Draw shaded fill area
        if len(points) > 1:
            poly_points = [pad_l, pad_t + plot_h]
            for px, py in points:
                poly_points.extend([px, py])
            poly_points.extend([points[-1][0], pad_t + plot_h])
            self.create_polygon(poly_points, fill="#E6F9F2", outline="")

        # Draw connecting line
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            self.create_line(x1, y1, x2, y2, fill=color, width=2)

        # Draw points and value labels
        for i, (px, py) in enumerate(points):
            self.create_oval(px - 3, py - 3, px + 3, py + 3, fill=color, outline="#FFFFFF", width=1)
            # Label
            val_str = f"{prefix}{int(y_values[i])}"
            self.create_text(px, py - 10, text=val_str, fill=THEME["text_dark"], font=(THEME["font_family"], 7, "bold"))
            # X label
            if i < len(x_labels):
                lbl = x_labels[i]
                short_lbl = lbl[5:] if len(lbl) >= 10 else lbl
                self.create_text(px, pad_t + plot_h + 14, text=short_lbl, fill=THEME["text_muted"], font=(THEME["font_family"], 7))
