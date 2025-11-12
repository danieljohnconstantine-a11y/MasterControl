import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict
from .columns import COLUMN_ORDER
from .validate_and_finalize import compute_speed_fields, validate_dataset, validate_consistency

def _audit(df: pd.DataFrame, output_dir: str, notes: List[str]) -> None:
    """Write audit log with timestamp, row count, missing columns, notes, and samples."""
    os.makedirs(os.path.join(output_dir, "logs"), exist_ok=True)
    audit_path = os.path.join(output_dir, "logs", "parse_audit.txt")
    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rows": int(len(df)),
        "missing_columns": [c for c in COLUMN_ORDER if c not in df.columns],
        "notes": notes,
        "samples": df.head(5).to_dict(orient="records"),
    }
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(f"📝 Audit written → {audit_path}")

def merge_sort_and_export(records: List[Dict], output_dir: str, docx_files: List[str] = None) -> None:
    """
    Consolidate records, enforce unified schema, sort, and export to Excel/CSV.
    
    Maintains audit logging and validation while using simplified sorting/export path.
    
    Args:
        records: List of dictionaries containing parsed data
        output_dir: Directory for output files
        docx_files: Optional list of DOCX file paths that were processed
    """
    if not records:
        print("⚠️ No records found to export.")
        _audit(pd.DataFrame(), output_dir, ["No records"])
        return

    # Create DataFrame from parsed records
    df = pd.DataFrame(records)
    
    # Ensure all 53 COLUMN_ORDER fields exist (add missing as empty strings)
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = ""
    
    # Compute speed fields from historical data
    df = compute_speed_fields(df)
    
    # Reindex to enforce unified column order
    df = df.reindex(columns=COLUMN_ORDER)
    
    # Convert Race_No and Box to numeric for proper sorting (coerce errors to NaN)
    df["Race_No"] = pd.to_numeric(df["Race_No"], errors="coerce")
    df["Box"] = pd.to_numeric(df["Box"], errors="coerce")
    
    # Sort by Track (alphabetical), Race_No (numeric), Box (numeric)
    df = df.sort_values(by=["Track", "Race_No", "Box"], ascending=[True, True, True])

    # Prepare output paths
    os.makedirs(output_dir, exist_ok=True)
    excel_path = os.path.join(output_dir, "all_dogs_master.xlsx")
    csv_path = os.path.join(output_dir, "all_dogs_master.csv")
    
    # Export to Excel with single sheet "All Data"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="All Data")
    
    # Export to CSV with UTF-8-BOM for Excel compatibility
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # Audit logging
    notes = [
        f"Exported columns={len(df.columns)} (unified schema with {len(COLUMN_ORDER)} fields).",
        "Sorted by Track → Race_No → Box.",
        "Unified single-sheet export; simplified sort/export path.",
        "Real DOCX data extracted with computed speed aggregation from historical rows.",
    ]
    _audit(df, output_dir, notes)
    
    # Validation reporting
    validate_dataset(df, output_dir)
    
    # Consistency check (DOCX vs Excel)
    if docx_files is not None:
        validate_consistency(df, output_dir, len(docx_files))
    
    print(f"✅ Unified Excel + CSV exported: {excel_path}")
