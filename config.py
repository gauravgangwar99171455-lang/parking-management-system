"""
ParkSmart Pro — Smart Parking Management System
Configuration Module
TQM Quality Attribute: Maintainability & Configurability (ISO/IEC 25010)
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "parksmart.db"
BACKUP_DIR = BASE_DIR / "backups"
TEMPLATES_DIR = BASE_DIR / "templates"
REPORTS_DIR = BASE_DIR / "reports"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "parksmart.log"

# Ensure runtime directories exist
for path in (DATA_DIR, BACKUP_DIR, TEMPLATES_DIR, REPORTS_DIR, LOG_DIR):
    path.mkdir(parents=True, exist_ok=True)

# Application Metadata
APP_NAME = "ParkSmart Pro"
APP_SUBTITLE = "Smart Parking Management System"
APP_VERSION = "1.0.0"
APP_AUTHOR = "B.Tech CSE Student (TQM Final Project)"
TQM_FRAMEWORK = "ISO 9001:2015 & ISO/IEC 25010 Compliant"

# UI Theme & Color Palette (Clean Modern Enterprise Flat Palette)
THEME = {
    "bg_main": "#F1F5F9",          # Cool light grey background
    "bg_card": "#FFFFFF",          # Pure white cards
    "bg_sidebar": "#0F172A",       # Deep navy slate
    "bg_sidebar_hover": "#1E293B", # Hover navy
    "bg_sidebar_active": "#2563EB",# Active blue accent
    "bg_header": "#FFFFFF",        # White top bar
    "text_dark": "#0F172A",        # Dark text
    "text_muted": "#64748B",       # Muted slate text
    "text_light": "#F8FAFC",       # White text for dark backgrounds
    "primary": "#2563EB",          # Royal blue
    "primary_hover": "#1D4ED8",
    "success": "#10B981",          # Emerald green (Available / Paid)
    "warning": "#F59E0B",          # Amber (Reserved / Warning)
    "danger": "#EF4444",           # Coral red (Occupied / Overdue)
    "info": "#06B6D4",             # Cyan
    "neutral": "#94A3B8",          # Maintenance / Out of service
    "border": "#E2E8F0",           # Subtle light border
    "font_family": "Segoe UI",     # Standard Windows modern font
    "font_mono": "Consolas",
}

# Vehicle Categories and defaults
DEFAULT_VEHICLE_CATEGORIES = [
    {"code": "TWO_WHEELER", "name": "Two-Wheeler / Bike", "icon": "🏍️", "default_rate": 1500, "base_rate": 2000},
    {"code": "CAR", "name": "Car / Sedan / Hatchback", "icon": "🚗", "default_rate": 3000, "base_rate": 4000},
    {"code": "SUV", "name": "SUV / MPV / Van", "icon": "🚙", "default_rate": 4000, "base_rate": 5000},
    {"code": "COMMERCIAL", "name": "Commercial / Bus / Truck", "icon": "🚚", "default_rate": 6000, "base_rate": 8000},
    {"code": "EV", "name": "Electric Vehicle (EV)", "icon": "⚡", "default_rate": 2500, "base_rate": 3500},
]

# Currency settings (Internally managed in minor units: cents/paise, e.g. 100 = 1.00)
CURRENCY_SYMBOL = "$"
CURRENCY_FACTOR = 100  # 100 minor units = 1.00 currency unit

# Security & Session Settings
PASSWORD_SALT_BYTES = 16
PBKDF2_ITERATIONS = 100_000
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME_SECONDS = 300

# Operational Quality Thresholds
DEFAULT_GRACE_PERIOD_MINUTES = 15
HIGH_OCCUPANCY_THRESHOLD = 0.85     # 85% occupancy triggers alert
CRITICAL_OCCUPANCY_THRESHOLD = 0.95 # 95% occupancy triggers critical alert
PAGINATION_DEFAULT_LIMIT = 25

# Performance Targets (as defined in TQM Quality Plan)
TARGET_SEARCH_LATENCY_MS = 200
TARGET_DASHBOARD_LOAD_MS = 500
TARGET_REPORT_LOAD_MS = 2000
TARGET_CSV_IMPORT_10K_SEC = 10.0
