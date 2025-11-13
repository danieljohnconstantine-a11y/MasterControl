"""
Export data to Excel and CSV using locked schema.
"""
import pandas as pd
import os
from datetime import datetime
from src.columns import COLUMN_ORDER


def merge_summary_and_aggregates(summary_rows: list, aggregates_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge summary rows with aggregated speed statistics.
    """
    # Convert summary to DataFrame
    df_summary = pd.DataFrame(summary_rows)
    
    if df_summary.empty:
        return pd.DataFrame(columns=COLUMN_ORDER)
    
    # Merge with aggregates if available
    if not aggregates_df.empty:
        merge_keys = ['Track', 'Race_Date', 'Race_No', 'Box', 'Dog_Name']
        df_merged = df_summary.merge(aggregates_df, on=merge_keys, how='left')
    else:
        df_merged = df_summary
    
    # Add Parse_Timestamp
    df_merged['Parse_Timestamp'] = datetime.now().isoformat()
    
    # Ensure all locked columns exist
    for col in COLUMN_ORDER:
        if col not in df_merged.columns:
            df_merged[col] = ""
    
    # Reindex to locked schema
    df_final = df_merged[COLUMN_ORDER].copy()
    
    # Remove exact duplicates
    dup_count = df_final.duplicated(subset=['Track', 'Race_Date', 'Race_No', 'Box', 'Dog_Name']).sum()
    df_final = df_final.drop_duplicates(subset=['Track', 'Race_Date', 'Race_No', 'Box', 'Dog_Name'], keep='first')
    
    # Sort
    df_final['Race_Date_dt'] = pd.to_datetime(df_final['Race_Date'], errors='coerce')
    df_final['Race_No_num'] = pd.to_numeric(df_final['Race_No'], errors='coerce')
    df_final['Box_num'] = pd.to_numeric(df_final['Box'], errors='coerce')
    
    df_final = df_final.sort_values(['Track', 'Race_Date_dt', 'Race_No_num', 'Box_num'])
    
    # Drop temporary sorting columns
    df_final = df_final[COLUMN_ORDER]
    
    return df_final, dup_count


def export_to_excel_csv(df: pd.DataFrame, output_dir: str = "outputs") -> dict:
    """
    Export DataFrame to Excel and CSV.
    
    Returns dict with export stats.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    excel_path = os.path.join(output_dir, "all_dogs_master.xlsx")
    csv_path = os.path.join(output_dir, "all_dogs_master.csv")
    
    # Export to Excel (single sheet "All Data")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All Data', index=False)
    
    # Export to CSV (UTF-8 BOM)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    stats = {
        'total_rows': len(df),
        'columns': len(df.columns),
        'excel_path': excel_path,
        'csv_path': csv_path,
    }
    
    return stats
