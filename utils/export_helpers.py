"""
ParkSmart Pro — CSV Export and Import Utilities
TQM Principle: Data Integrity & Prevention
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple

def export_rows_to_csv(filepath: Path, headers: List[str], rows: List[List[Any]]) -> Tuple[bool, str]:
    """Safely export data rows to CSV file."""
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return True, f"Successfully exported {len(rows)} rows to {filepath.name}"
    except Exception as e:
        return False, f"Failed to export CSV: {str(e)}"

def read_csv_records(filepath: Path) -> Tuple[bool, List[str], List[Dict[str, str]], str]:
    """Read CSV file and return header list and row dictionaries."""
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return False, [], [], f"File not found: {filepath}"
        
        with open(filepath, mode="r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = [h.strip() for h in (reader.fieldnames or [])]
            records = []
            for row in reader:
                cleaned_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k is not None}
                records.append(cleaned_row)
            return True, headers, records, f"Read {len(records)} records."
    except Exception as e:
        return False, [], [], f"Failed to read CSV: {str(e)}"
