import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict
from .columns import COLUMN_ORDER
from .validate_and_finalize import compute_speed_fields, validate_dataset, validate_consistency

def _audit(df: pd.DataFrame, output_dir: str, notes: List[str], summary_count: int = 0, history_count: int = 0) -> None:
    """Write audit log with timestamp, row count, missing columns, notes, and samples."""
    os.makedirs(os.path.join(output_dir, "logs"), exist_ok=True)
    audit_path = os.path.join(output_dir, "logs", "parse_audit.txt")
    
    # Calculate speed data statistics
    dogs_with_speed = 0
    if "Avg_Speed_km/h" in df.columns:
        dogs_with_speed = df["Avg_Speed_km/h"].notna().sum()
    
    speed_pct = (dogs_with_speed / len(df) * 100) if len(df) > 0 else 0
    
    # Calculate unique tracks
    unique_tracks = int(df["Track"].nunique()) if "Track" in df.columns and not df.empty else 0
    
    # Calculate unique meetings (Track + Race_Date combinations)
    unique_meetings = 0
    if "Track" in df.columns and "Race_Date" in df.columns and not df.empty:
        unique_meetings = int(df.groupby(["Track", "Race_Date"]).ngroups)
    
    # Calculate total unique dogs
    total_dogs = int(df["Dog_Name"].nunique()) if "Dog_Name" in df.columns and not df.empty else 0
    
    # Get top 5 tracks by dog count
    top_tracks = []
    if "Track" in df.columns and "Dog_Name" in df.columns and not df.empty:
        track_dog_counts = df.groupby("Track")["Dog_Name"].nunique().sort_values(ascending=False).head(5)
        top_tracks = [{"track": str(track), "dog_count": int(count)} for track, count in track_dog_counts.items()]
    
    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "total_rows": int(len(df)),
        "summary_rows": summary_count,
        "history_rows": history_count,
        "unique_tracks": unique_tracks,
        "unique_meetings": unique_meetings,
        "total_unique_dogs": total_dogs,
        "dogs_with_speed_data": int(dogs_with_speed),
        "speed_data_percentage": round(speed_pct, 1),
        "top_5_tracks_by_dog_count": top_tracks,
        "missing_columns": [c for c in COLUMN_ORDER if c not in df.columns],
        "notes": notes,
        "samples": df.head(5).to_dict(orient="records"),
    }
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(f"📝 Audit written → {audit_path}")

def merge_sort_and_export(summary_rows: List[Dict], history_rows: List[Dict], output_dir: str, docx_files: List[str] = None) -> None:
    """
    Consolidate summary and history records, merge them, enforce unified schema, sort, and export to Excel/CSV.
    
    Maintains audit logging and validation while using simplified sorting/export path.
    
    Args:
        summary_rows: List of dictionaries containing dog summary data (Groups A+B)
        history_rows: List of dictionaries containing historical race data (Group C)
        output_dir: Directory for output files
        docx_files: Optional list of DOCX file paths that were processed
    """
    if not summary_rows and not history_rows:
        print("⚠️ No records found to export.")
        _audit(pd.DataFrame(), output_dir, ["No records"], 0, 0)
        return

    # Create DataFrames from parsed records
    df_summary = pd.DataFrame(summary_rows) if summary_rows else pd.DataFrame()
    df_history = pd.DataFrame(history_rows) if history_rows else pd.DataFrame()
    
    # Merge summary and history data on Dog_Name and Tab_No
    if not df_summary.empty and not df_history.empty:
        # Merge history into summary, keeping all summary records
        df = pd.merge(df_summary, df_history, on=["Dog_Name", "Tab_No"], how="left", suffixes=('', '_hist'))
        # For columns that appear in both, prefer summary version (already done by suffixes)
        # Drop any _hist duplicates
        df = df[[c for c in df.columns if not c.endswith('_hist')]]
    elif not df_summary.empty:
        df = df_summary
    else:
        df = df_history
    
    # Add metadata fields
    parse_timestamp = datetime.now().isoformat(timespec="seconds")
    df["Parse_Timestamp"] = parse_timestamp
    
    # Add Data_Source_File from the original summary_rows if available
    # Otherwise, leave blank
    if not df.empty and "Data_Source_File" not in df.columns:
        df["Data_Source_File"] = ""
    
    # Ensure all COLUMN_ORDER fields exist (add missing as empty strings)
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = ""
    
    # Compute speed fields from historical data
    df = compute_speed_fields(df)
    
    # Reindex to enforce unified column order
    df = df.reindex(columns=COLUMN_ORDER)
    
    # Phase 6: Drop exact duplicates on key fields
    dedup_cols = ["Track", "Race_Date", "Race_No", "Box", "Dog_Name"]
    duplicates_before = len(df)
    df = df.drop_duplicates(subset=dedup_cols, keep="first")
    duplicates_dropped = duplicates_before - len(df)
    
    # Phase 6: Convert Race_Date to datetime for proper sorting
    if "Race_Date" in df.columns:
        df["Race_Date_Sort"] = pd.to_datetime(df["Race_Date"], errors="coerce")
    else:
        df["Race_Date_Sort"] = pd.NaT
    
    # Convert Race_No and Box to numeric for proper sorting (coerce errors to NaN)
    df["Race_No"] = pd.to_numeric(df["Race_No"], errors="coerce")
    df["Box"] = pd.to_numeric(df["Box"], errors="coerce")
    
    # Phase 6: Sort strictly by Track → Race_Date (as date) → Race_No (numeric) → Box (numeric)
    df = df.sort_values(
        by=["Track", "Race_Date_Sort", "Race_No", "Box"],
        ascending=[True, True, True, True],
        na_position="last"
    )
    
    # Drop the temporary sorting column
    df = df.drop(columns=["Race_Date_Sort"])

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
        f"Summary rows extracted: {len(summary_rows)}",
        f"History rows extracted: {len(history_rows)}",
        f"Dropped {duplicates_dropped} duplicate rows on (Track, Race_Date, Race_No, Box, Dog_Name).",
        "Sorted strictly by Track → Race_Date (as date) → Race_No (numeric) → Box (numeric).",
        "Final locked schema with metadata fields (Data_Source_File, Parse_Timestamp).",
        "Real DOCX data extracted with computed speed aggregation from historical rows.",
    ]
    _audit(df, output_dir, notes, len(summary_rows), len(history_rows))
    
    # Validation reporting
    validate_dataset(df, output_dir)
    
    # Consistency check (DOCX vs Excel)
    if docx_files is not None:
        validate_consistency(df, output_dir, len(docx_files))
    
    print(f"✅ Unified Excel + CSV exported: {excel_path}")
