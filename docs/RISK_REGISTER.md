# ParkSmart Pro — Project Risk Register & Failure Modes Analysis
**Subject:** Total Quality Management (TQM) — Risk Management (ISO 9001:2015 Clause 6.1)  

---

## 1. Risk Evaluation & Mitigation Matrix

| Risk ID | Failure Scenario / Risk Description | Severity (1-5) | Likelihood (1-5) | Risk Priority (S × L) | Preventive Control & Mitigation Strategy | Contingency / Fallback Plan |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **RSK-01** | **Database Lock Contention:** High concurrent check-in/out locks SQLite database file. | 4 | 2 | 8 | Enabled **WAL (Write-Ahead Logging)** mode via `PRAGMA journal_mode = WAL;` with `busy_timeout = 5000`. | Retry queue with exponential backoff on write attempts. |
| **RSK-02** | **Duplicate Active Admission:** Driver drives in and receives ticket, then attendant tries issuing second ticket. | 4 | 3 | 12 | Enforced SQLite Partial Unique Index `idx_unique_active_session` on active registrations. | UI displays alert stating active ticket number and timestamp. |
| **RSK-03** | **Financial Penny Rounding Errors:** Floating-point IEEE-754 inaccuracy during tariff/discount calculations. | 3 | 4 | 12 | **Integer Minor Currency:** All amounts stored as integer cents (`$15.50` stored as `1550`). | Auditing balance check before committing payment transaction. |
| **RSK-04** | **Corrupted Backup Restoration:** Restoring damaged backup wipes active operations. | 5 | 1 | 5 | **Safety Pre-Restore Snapshot:** System copies active DB to `pre_restore_safety_backup_*.db` before touching file. | Automated instant roll-back to safety snapshot if integrity check fails. |
| **RSK-05** | **Bulk Import Poisoning:** Uploading malformed CSV inserts partial/corrupt rows into production. | 4 | 3 | 12 | **Two-Phase Pre-Validation Engine:** Entire file dry-run checked against 12 schema rules; atomic single transaction. | User presented with line-by-line rejection table; DB untouched. |
| **RSK-06** | **Historical Rate Distortion:** Admin increases parking rates; past revenue reports recalculate with new rates. | 4 | 3 | 12 | **Immutable Tariff Snapshotting:** Sessions store JSON snapshot of rates active at settlement time. | Historical reports compute strictly from immutable transaction records. |
| **RSK-07** | **Brute-Force Authentication:** Unauthorized party attempts guessing operator passwords. | 4 | 2 | 8 | **Salted PBKDF2-HMAC-SHA256:** Rate-limiting lockout for 5 minutes after 5 consecutive failed attempts. | Administrative password reset required if persistent lockout occurs. |
| **RSK-08** | **Search Performance Degradation:** Database growth causes UI freezes during lookup. | 3 | 4 | 12 | **B-Tree Composite Indexes:** `idx_sessions_ticket`, `idx_sessions_reg` verified via `EXPLAIN QUERY PLAN`. | Automated benchmark script continuously verifies p95 latency < 200 ms. |
