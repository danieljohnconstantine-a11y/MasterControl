"""
Aggregate history rows to compute speed statistics per dog.
"""
import pandas as pd
from typing import List, Dict


def _to_seconds(time_str: str) -> float:
    """Convert time string (mm:ss.xx or ss.xx) to seconds."""
    if not time_str or not isinstance(time_str, str):
        return None
    
    time_str = time_str.strip()
    
    # Format: mm:ss.xx
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:
            try:
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            except:
                return None
    
    # Format: ss.xx
    try:
        return float(time_str)
    except:
        return None


def compute_speed(distance_m: float, time_seconds: float) -> float:
    """
    Compute speed in km/h from distance (meters) and time (seconds).
    Formula: (distance_m / time_seconds) * 3.6
    """
    if distance_m and time_seconds and time_seconds > 0:
        return (distance_m / time_seconds) * 3.6
    return None


def aggregate_history(history_rows: List[Dict]) -> pd.DataFrame:
    """
    Aggregate history rows to compute speed statistics.
    
    Returns DataFrame with columns:
        - Track, Race_Date, Race_No, Box, Dog_Name (grouping keys)
        - Hist_Count
        - Avg_Speed_km/h
        - Min_Speed_km/h
        - Max_Speed_km/h
    """
    if not history_rows:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(history_rows)
    
    # Compute speed for each history row
    speeds = []
    for _, row in df.iterrows():
        dist_str = row.get('Hist_Distance', '')
        time_str = row.get('Hist_Race_Time', '')
        
        dist_m = None
        if dist_str:
            try:
                dist_m = float(str(dist_str).replace('m', '').strip())
            except:
                pass
        
        time_sec = _to_seconds(time_str)
        speed = compute_speed(dist_m, time_sec)
        speeds.append(speed)
    
    df['Hist_Speed_km/h'] = speeds
    
    # Group by dog identity
    group_cols = ['Race_Track', 'Race_Date', 'Race_No', 'Box', 'Dog_Name']
    
    # Filter to only include rows with valid speeds
    df_with_speed = df[df['Hist_Speed_km/h'].notna()].copy()
    
    if df_with_speed.empty:
        return pd.DataFrame()
    
    # Aggregate
    agg_result = df_with_speed.groupby(group_cols, dropna=False).agg({
        'Hist_Speed_km/h': ['count', 'mean', 'min', 'max']
    }).reset_index()
    
    # Flatten column names
    agg_result.columns = [
        'Track', 'Race_Date', 'Race_No', 'Box', 'Dog_Name',
        'Hist_Count', 'Avg_Speed_km/h', 'Min_Speed_km/h', 'Max_Speed_km/h'
    ]
    
    return agg_result
