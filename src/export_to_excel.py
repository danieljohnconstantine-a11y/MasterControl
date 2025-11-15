"""
Export summary and history data to Excel and CSV with locked schema.
"""
import os
import pandas as pd
from datetime import datetime
from columns import COLUMN_ORDER


def merge_and_export(summary_rows, aggregates, output_dir='outputs'):
    """
    Merge summary rows with aggregates and export to Excel/CSV.
    
    Args:
        summary_rows: List of summary row dicts
        aggregates: Dict mapping dog keys to aggregate stats
        output_dir: Output directory path
        
    Returns:
        DataFrame of final exported data
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'logs'), exist_ok=True)
    
    if not summary_rows:
        # Create empty DataFrame with schema
        df = pd.DataFrame(columns=COLUMN_ORDER)
    else:
        # Convert to DataFrame
        df = pd.DataFrame(summary_rows)
        
        # Add aggregate statistics
        for idx, row in df.iterrows():
            key = (
                row.get('Track', ''),
                row.get('Race_Date', ''),
                row.get('Race_No', ''),
                row.get('Box', ''),
                row.get('Dog_Name', '')
            )
            
            if key in aggregates:
                agg = aggregates[key]
                df.at[idx, 'Hist_Count'] = agg.get('Hist_Count', '')
                df.at[idx, 'Avg_Speed_km/h'] = agg.get('Avg_Speed_km/h', '')
                df.at[idx, 'Min_Speed_km/h'] = agg.get('Min_Speed_km/h', '')
                df.at[idx, 'Max_Speed_km/h'] = agg.get('Max_Speed_km/h', '')
        
        # Add timestamp
        timestamp = datetime.now().isoformat()
        df['Parse_Timestamp'] = timestamp
        
        # Ensure all schema columns exist
        for col in COLUMN_ORDER:
            if col not in df.columns:
                df[col] = ''
        
        # Reindex to locked schema order
        df = df.reindex(columns=COLUMN_ORDER, fill_value='')
        
        # Remove duplicates
        key_cols = ['Track', 'Race_Date', 'Race_No', 'Box', 'Dog_Name']
        duplicates_before = len(df)
        df = df.drop_duplicates(subset=key_cols, keep='first')
        duplicates_dropped = duplicates_before - len(df)
        
        # Sort by Track, Race_Date, Race_No, Box
        df['Race_No'] = pd.to_numeric(df['Race_No'], errors='coerce')
        df['Box'] = pd.to_numeric(df['Box'], errors='coerce')
        df = df.sort_values(by=['Track', 'Race_Date', 'Race_No', 'Box'], na_position='last')
        df = df.reset_index(drop=True)
    
    # Export to Excel
    excel_path = os.path.join(output_dir, 'all_dogs_master.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='All Data')
    
    # Export to CSV with UTF-8-BOM
    csv_path = os.path.join(output_dir, 'all_dogs_master.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ Exported {len(df)} rows to {excel_path} and {csv_path}")
    
    return df
