# ParkSmart Pro — Database Architecture & Schema Specification
**Subject:** Total Quality Management (TQM) — Database Optimization  
**Engine:** SQLite 3 with WAL Mode, Foreign Keys Enforced, and Partial B-Tree Indexes  

---

## 1. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    ROLES ||--o{ USERS : "assigned to"
    USERS ||--o{ PARKING_SESSIONS : "created by"
    USERS ||--o{ PAYMENTS : "cashiered by"
    USERS ||--o{ AUDIT_LOGS : "performed by"
    USERS ||--o{ IMPORT_LOGS : "imported by"

    PARKING_ZONES ||--|{ PARKING_SLOTS : "contains"
    PARKING_SLOTS ||--o{ PARKING_SESSIONS : "hosts"
    PARKING_SLOTS ||--o{ RESERVATIONS : "reserved for"

    PARKING_SESSIONS ||--o{ PAYMENTS : "settled by"
    PARKING_SESSIONS }o--|| PARKING_TARIFFS : "applies snapshot of"

    ROLES {
        int id PK
        string name UK "admin | operator | auditor"
        string description
    }

    USERS {
        int id PK
        string username UK
        string password_hash
        string salt
        string full_name
        int role_id FK
        int is_active
        string last_login
    }

    PARKING_ZONES {
        int id PK
        string code UK "ZONE-A, ZONE-B, ..."
        string name
        int floor_number
        int is_active
    }

    PARKING_SLOTS {
        int id PK
        string slot_code UK "A-01, B-05, ..."
        int zone_id FK
        string supported_category "CAR | TWO_WHEELER | SUV | COMMERCIAL | EV"
        string status "AVAILABLE | OCCUPIED | RESERVED | MAINTENANCE"
        int is_active
    }

    PARKING_TARIFFS {
        int id PK
        string vehicle_category UK
        int base_duration_minutes
        int base_rate_cents
        int hourly_rate_cents
        int daily_max_cents
        int grace_period_minutes
        int lost_ticket_fee_cents
    }

    PARKING_SESSIONS {
        int id PK
        string ticket_number UK "TKT-YYYYMMDD-XXXX"
        string vehicle_registration
        string vehicle_category
        int slot_id FK
        string entry_time
        string exit_time
        string status "ACTIVE | COMPLETED | CANCELLED"
        int duration_minutes
        int gross_amount_cents
        int discount_cents
        int net_amount_cents
        string tariff_snapshot
    }

    RESERVATIONS {
        int id PK
        string reservation_code UK "RES-YYYYMMDD-XXXX"
        string customer_name
        string customer_phone
        string vehicle_registration
        string vehicle_category
        int slot_id FK
        string start_time
        string end_time
        string status "CONFIRMED | CHECKED_IN | CANCELLED | EXPIRED"
    }

    PAYMENTS {
        int id PK
        int session_id FK
        int amount_cents
        string payment_method "CASH | CARD | UPI | WALLET | WAIVED"
        string payment_status "PAID | REFUNDED | FAILED"
        string transaction_reference
        int cashier_user_id FK
        string payment_time
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK
        string username
        string action
        string entity_type
        string entity_id
        string details
        string created_at
    }

    IMPORT_LOGS {
        int id PK
        string import_type
        string filename
        int total_rows
        int successful_rows
        int failed_rows
        string error_summary
        int user_id FK
        string created_at
    }
```

---

## 2. Key Architectural Invariants & Constraints

### 1. Integer Minor Currency Representation
Floating-point arithmetic in software introduces precision errors (e.g. `0.1 + 0.2 = 0.30000000000000004`). In financial systems, this leads to penny rounding discrepancies.  
**ParkSmart Pro stores all currency as integer minor units (cents/paise):**
- `$25.50` is stored as integer `2550`.
- All multiplications and discounts use exact integer division with `round()`.

### 2. Double-Allocation Prevention (Partial Unique Index)
Standard table-level unique constraints cannot handle active vs historical status. ParkSmart Pro uses SQLite's **Partial Unique Index**:
```sql
CREATE UNIQUE INDEX idx_unique_active_slot_alloc 
    ON parking_sessions (slot_id) 
    WHERE status = 'ACTIVE';
```
*Effect:* Any attempt to assign an active ticket to an already active slot fails immediately at the database engine level, making race conditions impossible.

### 3. Duplicate Active Vehicle Prevention (Partial Unique Index)
```sql
CREATE UNIQUE INDEX idx_unique_active_session 
    ON parking_sessions (vehicle_registration) 
    WHERE status = 'ACTIVE';
```
*Effect:* A vehicle currently parked inside cannot be issued a second active parking ticket until its prior session is completed and paid.

### 4. Tariff Immutability Snapshotting
When a parking session is settled, the active tariff configuration is serialized into `tariff_snapshot` (JSON string). If an administrator later increases parking rates, historical revenue calculations and audit reports remain 100% historically immutable.

---

## 3. High-Performance Indexing Strategy

| Index Name | Target Table | Indexed Columns | Justification / Query Plan Impact |
| :--- | :--- | :--- | :--- |
| `idx_sessions_ticket` | `parking_sessions` | `(ticket_number)` | Enables $O(\log N)$ barcode scanner lookups during vehicle exit. |
| `idx_sessions_reg` | `parking_sessions` | `(vehicle_registration)` | Enables instantaneous search by vehicle license plate. |
| `idx_sessions_status` | `parking_sessions` | `(status)` | Accelerates active vs completed session partitioning. |
| `idx_sessions_entry` | `parking_sessions` | `(entry_time)` | Accelerates date-range reporting and daily inflow charts. |
| `idx_slots_zone_status` | `parking_slots` | `(zone_id, status)` | Powers real-time visual grid and zone occupancy counters. |
| `idx_reservations_overlap`| `reservations` | `(slot_id, status, start_time, end_time)` | Powers conflict detection engine for advance bookings. |
| `idx_audit_created` | `audit_logs` | `(created_at)` | Accelerates chronological audit trail inspection. |
