# ParkSmart Pro — Software Requirements Specification (SRS)
**Project Title:** ParkSmart Pro — Smart Parking Management System  
**Subject:** Total Quality Management (TQM) — Capstone College Project  
**Target Quality Standards:** ISO 9001:2015 (Quality Management) & ISO/IEC 25010 (Software Product Quality)  

---

## 1. Executive Summary & Problem Statement
Urban vehicular congestion and poorly managed parking facilities lead to severe resource wastage, inaccurate billing, revenue leakage, long customer wait times, and operational bottlenecks. 

**ParkSmart Pro** is an enterprise-grade desktop parking management system engineered specifically to embody **Total Quality Management (TQM)** principles: Customer Focus, Continuous Process Improvement (PDCA), Prevention rather than Correction, and Data-Driven Decision Making. It runs 100% locally on Windows with zero paid cloud dependencies, ensuring complete availability and cost-efficiency.

---

## 2. Stakeholder Profiles & User Roles

| Role | Responsibilities | Security Privileges |
| :--- | :--- | :--- |
| **Parking Operator** | Front-gate vehicle entry, exit settlement, physical bay guidance, ticket printing, customer queries. | Vehicle Entry, Exit/Billing, Slot View, Search, Reservations. |
| **System Administrator** | Parking policy management, rate configuration, user access, data imports, system backups. | Full Administrative Privileges across all modules. |
| **Quality Auditor** | Verification of financial books, compliance audits, performance profiling, error log inspection. | Read-Only access to Dashboard, Reports, Fast Search, and Audit Trail. |

---

## 3. Functional Requirements (FR)

### Module A: Dashboard & Analytics
- **FR-A1:** The system shall calculate live Key Performance Indicators (KPIs) directly via SQL queries on the active database without stale duplicate counters.
- **FR-A2:** Live KPIs must include: Total Spaces, Available Spaces, Occupied Spaces, Reserved Spaces, Maintenance Spaces, Occupancy Percentage, Entered Today, Exited Today, Currently Parked, Today's Net Revenue, Monthly Net Revenue, Average Duration, and Peak Parking Hours.
- **FR-A3:** The system shall render embedded dynamic vector charts displaying: (a) Occupancy Status Donut, (b) Active Vehicle Distribution by Category, and (c) 7-Day Revenue Trend Line.
- **FR-A4:** The system shall present a live feed of the 8 most recent vehicle movements with status badges.

### Module B: Parking Slot Management
- **FR-B1:** The system shall organize parking bays by Zone and Floor level (Basement, Ground, First Floor, Second Floor, Commercial Bay).
- **FR-B2:** Each slot must define its supported vehicle category: Two-Wheeler, Car/Sedan, SUV, Commercial, EV.
- **FR-B3:** Slots must maintain explicit states: `AVAILABLE`, `OCCUPIED`, `RESERVED`, `MAINTENANCE`.
- **FR-B4:** The system shall provide an interactive visual grid allowing operators and admins to inspect bay states and toggle maintenance modes.
- **FR-B5:** The system shall strictly reject double allocation of slots via database-level partial unique indexes.

### Module C: Vehicle Entry Management
- **FR-C1:** Operators shall input vehicle registration numbers with automatic normalization and regex validation.
- **FR-C2:** The system shall block admission if an active session already exists for the registration plate (`idx_unique_active_session`).
- **FR-C3:** The system shall auto-assign the optimal available slot or allow manual allocation from eligible bays.
- **FR-C4:** The system shall generate a unique ticket formatted as `TKT-YYYYMMDD-XXXX` and open a printable ticket modal.

### Module D: Vehicle Exit & Automated Billing
- **FR-D1:** Search active sessions by scanning ticket number or typing registration plate.
- **FR-D2:** Compute exact duration between entry and exit timestamps.
- **FR-D3:** Enforce configured tariff rules: free grace period, base fee for initial duration, hourly incremental fee, and daily maximum cap.
- **FR-D4:** Support authorized discounts (Staff 50%, Senior 25%, Frequent Parker 15%, Student 20%, Waived 100%).
- **FR-D5:** Process checkout, payment logging, slot release, and session completion in a single atomic database transaction.

### Module E: Fast Search Engine
- **FR-E1:** Provide multi-criteria search filtering by registration, ticket number, slot code, status, category, and date range.
- **FR-E2:** Display query execution latency in milliseconds using high-precision timers.
- **FR-E3:** Paginate results with configurable page sizes (15, 25, 50, 100) and column sorting.
- **FR-E4:** Provide an embedded SQLite `EXPLAIN QUERY PLAN` inspector for performance verification.

### Module F: Advance Reservations
- **FR-F1:** Allow booking parking bays for future datetime windows `[start_time, end_time]`.
- **FR-F2:** Detect and block overlapping bookings on the same bay.
- **FR-F3:** Support 1-click check-in from reservation into an active admission ticket.
- **FR-F4:** Enable cancellation of reservations with slot release.

### Module G: Tariff Configuration
- **FR-G1:** Administrators shall configure base rates, hourly rates, daily caps, grace periods, and lost ticket fees per vehicle category.
- **FR-G2:** Historical parking sessions must preserve the snapshot of tariff rates active at billing time, guaranteeing historical immutability.

### Module H: CSV Import / Export Engine
- **FR-H1:** Support bulk import of parking slot master data and historical completed sessions.
- **FR-H2:** Execute a 12-point pre-validation process before touching the database (header check, data types, duplicate check, zone existence).
- **FR-H3:** Present an interactive diagnostic preview showing valid counts, invalid counts, and specific line-by-line rejection reasons.
- **FR-H4:** Atomically commit valid rows in a single database transaction.

### Module I: Analytical Reports
- **FR-I1:** Generate date-filtered reports for completed sessions, revenue by vehicle type, and revenue by payment method.
- **FR-I2:** Present parking duration distribution bucket charts.
- **FR-I3:** Export generated reports to CSV files.

### Module J: Alerts & Notifications
- **FR-J1:** Display high occupancy warning when bays exceed 85% utilization.
- **FR-J2:** Display critical capacity alert when 0 bays remain available.

### Module K: Security & User Management
- **FR-K1:** Salted PBKDF2-HMAC-SHA256 password storage (100,000 iterations).
- **FR-K2:** Rate limiting and temporary lockout after 5 consecutive failed login attempts.
- **FR-K3:** Role-based access control protecting administrative modules.

### Module L: Audit Trail
- **FR-L1:** Immutable audit log capturing user ID, username, action type, entity type, target ID, and JSON operational payload.

### Module M: Backup & Disaster Recovery
- **FR-M1:** Execute live, non-blocking online backups using SQLite's backup API.
- **FR-M2:** Verify backup corruption status via `PRAGMA integrity_check`.
- **FR-M3:** Automatically generate an emergency safety snapshot before restoring any database backup.

---

## 4. Non-Functional Requirements (NFR)

| Metric | Requirement | Target Standard |
| :--- | :--- | :--- |
| **Performance (Search)** | Common vehicle search query latency p95 < 200 ms on 10,000 records. | ISO/IEC 25010 Performance Efficiency |
| **Performance (Dashboard)** | Full dashboard aggregation load time < 500 ms. | ISO/IEC 25010 Performance Efficiency |
| **Reliability (ACID)** | Zero duplicate active tickets, zero duplicate slot assignments, zero ghost payments. | ISO/IEC 25010 Reliability |
| **Usability** | Clear color contrast, keyboard-accessible shortcuts (Enter to submit), status badges. | ISO/IEC 25010 Usability |
| **Portability** | Runs natively on Windows 10/11 with zero external cloud dependencies or paid APIs. | ISO/IEC 25010 Portability |
| **Maintainability** | Clean separation of concerns (Database, Models, Services, UI Components, Views). | ISO/IEC 25010 Maintainability |
