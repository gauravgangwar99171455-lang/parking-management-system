# ParkSmart Pro — User Operations Manual
**Desktop Application Guide for Parking Operators, Auditors, and Administrators**

---

## 1. System Requirements & Launching

### System Requirements:
- **Operating System:** Windows 10, Windows 11 (or compatible Linux / macOS).
- **Runtime:** Python 3.10+ (Standard Library).
- **Dependencies:** Self-contained zero external cloud dependencies.

### Launching the Application:
Open PowerShell or Command Prompt, navigate to the project directory, and run:
```powershell
python main.py
```

---

## 2. Authentication & Roles

| Role | Username | Default Password | Recommended Usage |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin` | `admin123` | Full access to tariffs, backups, user accounts, and imports. |
| **Front Desk Operator** | `operator` | `operator123` | Vehicle check-in, exit billing, reservations, and slot view. |
| **Quality Auditor** | `auditor` | `auditor123` | Read-only access to dashboard, search, reports, and audit trail. |

*Note: The login screen features convenient 1-click credential autofill buttons for rapid demonstration.*

---

## 3. Core Operator Workflows

### Workflow 1: Admitting a Vehicle (Check-In)
1. Navigate to **📥 Vehicle Entry** from the sidebar.
2. Enter the vehicle license plate (e.g., `KA-01-AB-1234`). Real-time validation confirms valid formatting.
3. Select the vehicle category: **Car / Sedan**, **Two-Wheeler**, **SUV**, **Commercial**, or **EV**.
4. Choose slot allocation mode:
   - **Auto-Assign (Default):** The system automatically assigns the closest available bay for that vehicle type.
   - **Manual:** Select a specific vacant bay from the dropdown.
5. Click **Generate Admission Ticket & Open Barrier ➔**.
6. The official **Parking Admission Ticket** modal appears with barcode graphic, allocated slot, and timestamp. Click **Print Ticket** or **Close**.

### Workflow 2: Processing Vehicle Exit & Settlement (Check-Out)
1. Navigate to **📤 Vehicle Exit & Pay** from the sidebar.
2. Scan the ticket barcode or type the license plate into the search bar, then click **Look Up Active Session** (or press Enter).
3. The system displays:
   - Vehicle details, bay location, and exact elapsed duration.
   - Calculated gross parking charges according to vehicle rates.
4. If applicable, select an **Authorized Discount** (e.g., *Campus Staff 50%*, *Senior Citizen 25%*). The net total recalculates instantly.
5. Choose the **Payment Method** (*Cash*, *Card*, *UPI*, or *Mobile Wallet*).
6. Click **Settle Payment & Release Slot ➔**.
7. The **Official Parking Payment Receipt** modal appears with financial breakdown and cashier audit signature. The parking bay is freed immediately for other vehicles.

### Workflow 3: Booking an Advance Reservation
1. Navigate to **📅 Reservations** from the sidebar.
2. Fill in the customer name, phone number, vehicle plate, vehicle type, and target date/time window.
3. Select an available bay and click **Confirm Reservation ➔**.
4. When the customer arrives, select their booking from the list and click **Check-In Vehicle** to generate their admission ticket.

---

## 4. Administrator Workflows

### Workflow 1: Managing Parking Tariffs
1. Navigate to **💲 Tariffs & Rates** from the sidebar (Admin access required).
2. Select a vehicle category from the table.
3. Adjust the base rate, base duration (minutes), hourly incremental fee, daily maximum cap, or grace period.
4. Click **Save Tariff Changes**. New rates take effect for all subsequent check-ins.

### Workflow 2: Creating Backups & Restoring
1. Navigate to **💾 Backup & Recovery** from the sidebar.
2. Click **➕ Create Live Backup Now**. The system creates a timestamped, verified SQLite snapshot.
3. To restore an earlier snapshot, select the backup file and click **⚠️ Restore Selected Snapshot**.
   - *TQM Failsafe:* ParkSmart Pro automatically generates an emergency safety snapshot of the active database before restoration begins.

### Workflow 3: Bulk Data Import
1. Navigate to **📂 CSV Import & Export** from the sidebar.
2. Select import type (**PARKING_SLOTS** or **HISTORICAL_SESSIONS**).
3. Click **📁 Select CSV File & Validate**.
4. The system runs diagnostic pre-validation, displaying valid counts, rejected rows, and specific line-by-line error explanations.
5. If clean, click **Confirm & Import Valid Records ➔**. All records are inserted in a single atomic transaction.
