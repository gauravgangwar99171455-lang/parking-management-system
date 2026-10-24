# ParkSmart Pro — Software Architecture & Technical Design
**Standard:** ISO/IEC 25010 Software Architecture & Quality Characteristics  

---

## 1. High-Level Architectural Diagram

ParkSmart Pro employs a modular, layered desktop architecture separating presentation, business logic, domain models, and data persistence:

```mermaid
flowchart TD
    subgraph Presentation Layer (Tkinter / TTK)
        App["ParkSmartApp (ui/app.py)"]
        Nav["TopNavBar & Sidebar"]
        Views["Dashboard, Slots, Entry, Exit, Search, Reports, Tariffs, Imports, Users, Backup"]
        Comps["KPICards, Vector Charts, PaginatedTable, Dialogs, AlertBanner"]
    end

    subgraph Service Layer (Business Logic & Transactions)
        AuthSvc["AuthService"]
        ParkSvc["ParkingService"]
        BillSvc["BillingService"]
        ResSvc["ReservationService"]
        SearchSvc["SearchService"]
        RepSvc["ReportService"]
        ImpSvc["ImportService"]
        BackSvc["BackupService"]
        AuditSvc["AuditService"]
    end

    subgraph Domain Models
        Models["User, ParkingZone, ParkingSlot, ParkingSession, Reservation, ParkingTariff, Payment, AuditLog"]
    end

    subgraph Persistence Layer (SQLite 3 WAL)
        Conn["Connection Factory (PRAGMA foreign_keys = ON, WAL Mode)"]
        Schema["schema.sql (Partial Unique Indexes, Constraints)"]
        Migrations["Integrity Checks & Backup API"]
        DB[(parksmart.db)]
    end

    App --> Nav
    App --> Views
    Views --> Comps
    Views --> ServiceLayer["Services"]
    ServiceLayer --> Models
    ServiceLayer --> Conn
    Conn --> Schema
    Conn --> DB
```

---

## 2. Layer Responsibilities

### 1. Presentation Layer (`ui/`)
- Pure desktop user interface built with Tkinter and TTK.
- Never directly writes raw SQL queries; delegates entirely to the Service Layer.
- Employs modular view components (`ui/views/`) and reusable widgets (`ui/components/`).
- Includes a native Tkinter vector graphics engine for donut charts, bar charts, and trend lines.

### 2. Service Layer (`services/`)
- Encapsulates all business rules, tariff calculation algorithms, reservation conflict detection, and audit logging.
- Manages atomic transactions: coordinates multiple database operations into single commit/rollback blocks.
- Pre-validates inputs before invoking database queries.

### 3. Domain Model Layer (`models/`)
- Strongly typed Python `@dataclass` structures representing domain entities.
- Implements `from_row()` deserializers with fallback defaults for missing optional columns.
- Implements `to_snapshot()` serializers for immutable JSON audit snapshots.

### 4. Persistence Layer (`database/`)
- SQLite 3 with Write-Ahead Logging (WAL) and synchronous=NORMAL.
- Enforces relational invariants at the database engine level via foreign keys and partial unique indexes.
- Online non-locking backups using `sqlite3.Connection.backup()`.
