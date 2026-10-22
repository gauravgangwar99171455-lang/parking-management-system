"""
ParkSmart Pro — Main Application Window Orchestrator
TQM Quality Attribute: Usability, Fault Tolerance & RBAC Access Protection
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME, APP_NAME, APP_SUBTITLE, APP_VERSION
from database.connection import init_database
from services.auth_service import auth_service
from services.report_service import report_service
from ui.theme import setup_styles
from ui.components.navbar import TopNavBar
from ui.components.sidebar import Sidebar
from ui.components.toast import AlertBanner
from ui.views.login_view import LoginView
from ui.views.dashboard_view import DashboardView
from ui.views.slots_view import SlotsView
from ui.views.vehicle_entry_view import VehicleEntryView
from ui.views.vehicle_exit_view import VehicleExitView
from ui.views.search_view import SearchView
from ui.views.reservations_view import ReservationsView
from ui.views.tariffs_view import TariffsView
from ui.views.reports_view import ReportsView
from ui.views.imports_view import ImportsView
from ui.views.users_view import UsersView
from ui.views.audit_view import AuditView
from ui.views.backup_view import BackupView

class ParkSmartApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — {APP_SUBTITLE} (v{APP_VERSION})")
        self.geometry("1280x820")
        self.minsize(1050, 680)
        self.configure(bg=THEME["bg_main"])

        # Setup modern styles
        setup_styles(self)

        # Ensure database is initialized
        init_database(seed_defaults=True)

        self.current_user = None
        self.active_view_key = "dashboard"

        # Container for views
        self.root_container = tk.Frame(self, bg=THEME["bg_main"])
        self.root_container.pack(fill="both", expand=True)

        # Show Login Screen first
        self._show_login_screen()

    def _show_login_screen(self):
        for w in self.root_container.winfo_children():
            w.destroy()

        self.login_view = LoginView(self.root_container, on_login_success=self._on_login_success)
        self.login_view.pack(fill="both", expand=True)

    def _on_login_success(self, user):
        self.current_user = user
        self._build_main_workspace()
        self.navigate_to("dashboard")
        self._check_operational_alerts()

    def _build_main_workspace(self):
        for w in self.root_container.winfo_children():
            w.destroy()

        # Workspace Container: Left Sidebar + Right Main Area
        self.main_split = tk.Frame(self.root_container, bg=THEME["bg_main"])
        self.main_split.pack(fill="both", expand=True)

        # 1. Left Sidebar
        self.sidebar = Sidebar(self.main_split, on_navigate=self.navigate_to)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.update_role(self.current_user.role_name)

        # 2. Right Main Layout
        self.right_area = tk.Frame(self.main_split, bg=THEME["bg_main"])
        self.right_area.pack(side="right", fill="both", expand=True)

        # 2a. Top Navigation Bar
        self.navbar = TopNavBar(self.right_area, on_logout=self._do_logout)
        self.navbar.pack(fill="x", side="top")
        self.navbar.set_user_info(self.current_user.full_name, self.current_user.role_name)

        # 2b. Global Alert Banner
        self.alert_banner = AlertBanner(self.right_area)

        # 2c. View Container
        self.view_container = tk.Frame(self.right_area, bg=THEME["bg_main"])
        self.view_container.pack(fill="both", expand=True)

        # Instantiate View Singletons
        self.views = {
            "dashboard": DashboardView(self.view_container, on_navigate=self.navigate_to),
            "slots": SlotsView(self.view_container, on_navigate=self.navigate_to),
            "entry": VehicleEntryView(self.view_container, on_navigate=self.navigate_to),
            "exit": VehicleExitView(self.view_container, on_navigate=self.navigate_to),
            "search": SearchView(self.view_container, on_navigate=self.navigate_to),
            "reservations": ReservationsView(self.view_container, on_navigate=self.navigate_to),
            "tariffs": TariffsView(self.view_container, on_navigate=self.navigate_to),
            "reports": ReportsView(self.view_container, on_navigate=self.navigate_to),
            "imports": ImportsView(self.view_container, on_navigate=self.navigate_to),
            "users": UsersView(self.view_container, on_navigate=self.navigate_to),
            "audit": AuditView(self.view_container, on_navigate=self.navigate_to),
            "backup": BackupView(self.view_container, on_navigate=self.navigate_to),
        }

    def navigate_to(self, view_key: str):
        if view_key not in self.views:
            return

        # RBAC Check
        admin_only_views = ("tariffs", "imports", "users", "backup")
        if view_key in admin_only_views and not self.current_user.is_admin():
            messagebox.showwarning("Access Denied", "This module requires Administrator security clearance.")
            return

        self.active_view_key = view_key
        self.sidebar.set_active(view_key)

        title_map = {
            "dashboard": "Operational Dashboard & Real-Time Analytics",
            "slots": "Parking Slot Management & Visual Bay Layout",
            "entry": "Vehicle Entry Registration & Ticket Issuance",
            "exit": "Vehicle Exit Checkout & Automated Payment Settlement",
            "search": "Fast Vehicle Search & Query Profiler",
            "reservations": "Advance Parking Reservations & Space Bookings",
            "tariffs": "Parking Tariff & Billing Rates Configuration",
            "reports": "Comprehensive Financial & Utilization Reports",
            "imports": "CSV Data Import & Export Engine",
            "users": "System Users & Role-Based Access Control",
            "audit": "Immutable System Audit Trail",
            "backup": "Database Backup & Disaster Recovery Management",
        }
        self.navbar.set_view_title(title_map.get(view_key, "ParkSmart Pro"))

        # Hide all views and show selected
        for k, v in self.views.items():
            if k == view_key:
                v.pack(fill="both", expand=True)
                # Call view refresh hook if present
                if hasattr(v, "refresh_data"):
                    v.refresh_data()
                elif hasattr(v, "refresh_slots"):
                    v.refresh_slots()
                elif hasattr(v, "refresh_view"):
                    v.refresh_view()
                elif hasattr(v, "refresh_reservations"):
                    v.refresh_reservations()
                elif hasattr(v, "refresh_tariffs"):
                    v.refresh_tariffs()
                elif hasattr(v, "generate_report"):
                    v.generate_report()
                elif hasattr(v, "refresh_users"):
                    v.refresh_users()
                elif hasattr(v, "refresh_logs"):
                    v.refresh_logs()
                elif hasattr(v, "refresh_backups"):
                    v.refresh_backups()
                elif hasattr(v, "do_search"):
                    v.do_search(1)
            else:
                v.pack_forget()

    def _check_operational_alerts(self):
        """Monitor capacity and upcoming reservations periodically."""
        try:
            kpis = report_service.get_dashboard_kpis()
            tot = kpis["total_slots"]
            occ = kpis["occupied_slots"]
            rate = kpis["occupancy_percentage"]
            avail = kpis["available_slots"]

            if avail == 0 and tot > 0:
                self.navbar.set_alert("PARKING FULL: 0 Available Slots", is_critical=True)
                self.alert_banner.show("🚨 Critical Capacity Alert: All parking slots are occupied!", level="danger")
            elif rate >= 85.0:
                self.navbar.set_alert(f"HIGH OCCUPANCY ({rate}%)", is_critical=False)
                self.alert_banner.show(f"⚠️ Capacity Warning: Parking occupancy has reached {rate}%. Only {avail} slots remain.", level="warning")
            else:
                self.navbar.set_alert("")
                self.alert_banner.hide()
        except Exception:
            pass

        # Check every 30 seconds
        self.after(30000, self._check_operational_alerts)

    def _do_logout(self):
        if messagebox.askyesno("Confirm Sign Out", "Are you sure you want to sign out of ParkSmart Pro?"):
            auth_service.logout()
            self.current_user = None
            self._show_login_screen()

def main():
    app = ParkSmartApp()
    app.mainloop()

if __name__ == "__main__":
    main()
