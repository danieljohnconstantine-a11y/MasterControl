"""
Export Module
Responsibility: Export summary data to Excel and CSV using locked schema
"""
import pandas as pd
import os
from src.columns import COLUMN_ORDER


def export_to_excel_csv(summary_rows, output_dir="outputs"):
    """
    Export summary rows to Excel and CSV with locked 58-column schema.
    
    Args:
        summary_rows: List of dog summary dicts
        output_dir: Output directory path
        
    Returns:
        tuple: (excel_path, csv_path, export_stats)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(summary_rows)
    
    # Ensure all locked columns exist (fill missing with empty string)
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = ""
    
    # Reindex to locked column order
    df = df[COLUMN_ORDER]
    
    # Drop exact duplicates on key fields
    key_fields = ["Track", "Race_Date", "Race_No", "Box", "Dog_Name"]
    initial_count = len(df)
    df = df.drop_duplicates(subset=key_fields, keep="first")
    duplicates_dropped = initial_count - len(df)
    
    # Sort by Track, Race_Date, Race_No, Box
    # Convert Race_No and Box to numeric for proper sorting
    df["Race_No_Sort"] = pd.to_numeric(df["Race_No"], errors="coerce")
    df["Box_Sort"] = pd.to_numeric(df["Box"], errors="coerce")
    
    # Convert Race_Date to datetime for proper sorting
    df["Race_Date_Sort"] = pd.to_datetime(df["Race_Date"], errors="coerce")
    
    # Sort
    df = df.sort_values(
        by=["Track", "Race_Date_Sort", "Race_No_Sort", "Box_Sort"],
        na_position="last"
    )
    
    # Drop sort helper columns
    df = df.drop(columns=["Race_No_Sort", "Box_Sort", "Race_Date_Sort"])
    
    # Export to Excel
    excel_path = os.path.join(output_dir, "all_dogs_master.xlsx")
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="All Data")
    
    # Export to CSV with UTF-8-BOM encoding
    csv_path = os.path.join(output_dir, "all_dogs_master.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    # Compute export stats
    export_stats = {
        "total_rows": len(df),
        "duplicates_dropped": duplicates_dropped,
        "unique_tracks": df["Track"].nunique(),
        "unique_meetings": df.groupby(["Track", "Race_Date"]).ngroups if len(df) > 0 else 0,
        "columns_exported": len(COLUMN_ORDER),
        "dogs_with_speed_data": len(df[df["Avg_Speed_km/h"] != ""])
    }
    
    return excel_path, csv_path, export_stats
