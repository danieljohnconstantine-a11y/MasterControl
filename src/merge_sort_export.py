"""
Module for merging, sorting, and exporting greyhound data.
"""
import pandas as pd
import os


def merge_sort_and_export(records, output_dir):
    """
    Merge all records, sort them, and export to CSV and Excel formats.
    
    Args:
        records (list): List of dictionaries containing dog records
        output_dir (str): Directory path where output files will be saved
    """
    if not records:
        print("⚠️ No records to export.")
        return
    
    # Create DataFrame from records
    df = pd.DataFrame(records)
    
    # Sort by Box number if available
    if 'Box' in df.columns:
        df = df.sort_values('Box')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Export to CSV
    csv_path = os.path.join(output_dir, 'greyhound_data.csv')
    df.to_csv(csv_path, index=False)
    print(f"✅ Exported CSV: {csv_path}")
    
    # Export to Excel
    excel_path = os.path.join(output_dir, 'greyhound_data.xlsx')
    df.to_excel(excel_path, index=False, engine='openpyxl')
    print(f"✅ Exported Excel: {excel_path}")
    
    print(f"📊 Total records exported: {len(df)}")
