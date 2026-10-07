-- ============================================================================
-- ParkSmart Pro — High-Performance Normalized Database Schema
-- TQM Quality Attributes: Data Integrity, ACID Compliance, Query Optimization
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. Roles Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL CHECK(name IN ('admin', 'operator', 'auditor')),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 2. Users Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    last_login TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 3. Parking Zones Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parking_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    floor_number INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 4. Parking Slots Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parking_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_code TEXT UNIQUE NOT NULL,
    zone_id INTEGER NOT NULL REFERENCES parking_zones(id) ON DELETE RESTRICT,
    supported_category TEXT NOT NULL CHECK(supported_category IN ('TWO_WHEELER', 'CAR', 'SUV', 'COMMERCIAL', 'EV')),
    status TEXT NOT NULL CHECK(status IN ('AVAILABLE', 'OCCUPIED', 'RESERVED', 'MAINTENANCE')) DEFAULT 'AVAILABLE',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 5. Parking Tariffs Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parking_tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_category TEXT UNIQUE NOT NULL CHECK(vehicle_category IN ('TWO_WHEELER', 'CAR', 'SUV', 'COMMERCIAL', 'EV')),
    base_duration_minutes INTEGER NOT NULL DEFAULT 60 CHECK(base_duration_minutes >= 0),
    base_rate_cents INTEGER NOT NULL DEFAULT 2000 CHECK(base_rate_cents >= 0),
    hourly_rate_cents INTEGER NOT NULL DEFAULT 1000 CHECK(hourly_rate_cents >= 0),
    daily_max_cents INTEGER NOT NULL DEFAULT 6000 CHECK(daily_max_cents >= 0),
    grace_period_minutes INTEGER NOT NULL DEFAULT 15 CHECK(grace_period_minutes >= 0),
    lost_ticket_fee_cents INTEGER NOT NULL DEFAULT 5000 CHECK(lost_ticket_fee_cents >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 6. Parking Sessions Table (Core Transactional Table)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parking_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number TEXT UNIQUE NOT NULL,
    vehicle_registration TEXT NOT NULL,
    vehicle_category TEXT NOT NULL CHECK(vehicle_category IN ('TWO_WHEELER', 'CAR', 'SUV', 'COMMERCIAL', 'EV')),
    slot_id INTEGER NOT NULL REFERENCES parking_slots(id) ON DELETE RESTRICT,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')) DEFAULT 'ACTIVE',
    duration_minutes INTEGER DEFAULT 0 CHECK(duration_minutes >= 0),
    gross_amount_cents INTEGER DEFAULT 0 CHECK(gross_amount_cents >= 0),
    discount_cents INTEGER DEFAULT 0 CHECK(discount_cents >= 0),
    net_amount_cents INTEGER DEFAULT 0 CHECK(net_amount_cents >= 0),
    tariff_snapshot TEXT, -- JSON snapshot of applied rates at billing time
    discount_reason TEXT,
    notes TEXT,
    created_by_user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 7. Parking Reservations Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_code TEXT UNIQUE NOT NULL,
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    vehicle_registration TEXT NOT NULL,
    vehicle_category TEXT NOT NULL CHECK(vehicle_category IN ('TWO_WHEELER', 'CAR', 'SUV', 'COMMERCIAL', 'EV')),
    slot_id INTEGER NOT NULL REFERENCES parking_slots(id) ON DELETE RESTRICT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('CONFIRMED', 'CHECKED_IN', 'CANCELLED', 'EXPIRED')) DEFAULT 'CONFIRMED',
    notes TEXT,
    created_by_user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 8. Payments Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES parking_sessions(id) ON DELETE RESTRICT,
    amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0),
    payment_method TEXT NOT NULL CHECK(payment_method IN ('CASH', 'CARD', 'UPI', 'WALLET', 'WAIVED')),
    payment_status TEXT NOT NULL CHECK(payment_status IN ('PAID', 'REFUNDED', 'FAILED')) DEFAULT 'PAID',
    transaction_reference TEXT,
    cashier_user_id INTEGER REFERENCES users(id),
    payment_time TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 9. Audit Logs Table (Tamper-Resistant Historical Trail)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    username TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 10. Import Logs Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS import_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    successful_rows INTEGER NOT NULL DEFAULT 0,
    failed_rows INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- ============================================================================
-- PERFORMANCE OPTIMIZATION INDEXES & CONSTRAINTS
-- ============================================================================

-- TQM Safety Invariant 1: Prevent duplicate active parking sessions for the same vehicle
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_session 
    ON parking_sessions (vehicle_registration) 
    WHERE status = 'ACTIVE';

-- TQM Safety Invariant 2: Prevent concurrent allocation of a slot to multiple active sessions
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_slot_alloc 
    ON parking_sessions (slot_id) 
    WHERE status = 'ACTIVE';

-- High-Frequency Search Optimization Indexes
CREATE INDEX IF NOT EXISTS idx_sessions_ticket ON parking_sessions (ticket_number);
CREATE INDEX IF NOT EXISTS idx_sessions_reg ON parking_sessions (vehicle_registration);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON parking_sessions (status);
CREATE INDEX IF NOT EXISTS idx_sessions_entry ON parking_sessions (entry_time);
CREATE INDEX IF NOT EXISTS idx_sessions_exit ON parking_sessions (exit_time);
CREATE INDEX IF NOT EXISTS idx_sessions_category ON parking_sessions (vehicle_category);

CREATE INDEX IF NOT EXISTS idx_slots_zone_status ON parking_slots (zone_id, status);
CREATE INDEX IF NOT EXISTS idx_slots_category_status ON parking_slots (supported_category, status);

CREATE INDEX IF NOT EXISTS idx_reservations_overlap ON reservations (slot_id, status, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_reservations_reg ON reservations (vehicle_registration);

CREATE INDEX IF NOT EXISTS idx_payments_session ON payments (session_id);
CREATE INDEX IF NOT EXISTS idx_payments_time ON payments (payment_time);

CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs (action);
