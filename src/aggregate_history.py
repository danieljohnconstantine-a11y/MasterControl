"""
Aggregate historical race data to compute speed statistics per dog.
"""
import re


def _to_seconds(time_str):
    """Convert time string (mm:ss.xx or ss.xx) to seconds."""
    if not time_str or not isinstance(time_str, str):
        return None
    
    time_str = time_str.strip()
    
    # Handle mm:ss.xx format
    if ':' in time_str:
        try:
            parts = time_str.split(':')
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        except:
            return None
    
    # Handle ss.xx format
    try:
        return float(time_str)
    except:
        return None


def compute_speed(distance_m, time_seconds):
    """
    Compute speed in km/h from distance (meters) and time (seconds).
    Formula: (distance_m / time_seconds) * 3.6
    """
    if not distance_m or not time_seconds or time_seconds <= 0:
        return None
    
    try:
        distance_m = float(distance_m)
        time_seconds = float(time_seconds)
        return (distance_m / time_seconds) * 3.6
    except:
        return None


def aggregate_history(summary_rows, history_rows):
    """
    Aggregate history rows by dog and compute speed statistics.
    
    Args:
        summary_rows: List of summary row dicts
        history_rows: List of history row dicts
        
    Returns:
        Dict mapping dog keys to speed aggregates
    """
    # Group history by dog
    from collections import defaultdict
    history_by_dog = defaultdict(list)
    
    for hist in history_rows:
        key = (
            hist.get('Track', ''),
            hist.get('Race_Date', ''),
            hist.get('Race_No', ''),
            hist.get('Box', ''),
            hist.get('Dog_Name', '')
        )
        
        # Compute speed for this history row
        dist = hist.get('Hist_Distance')
        time = hist.get('Hist_Race_Time')
        
        if dist and time:
            time_sec = _to_seconds(time)
            speed = compute_speed(dist, time_sec)
            if speed:
                history_by_dog[key].append(speed)
    
    # Compute aggregates
    aggregates = {}
    for key, speeds in history_by_dog.items():
        if speeds:
            aggregates[key] = {
                'Hist_Count': len(speeds),
                'Avg_Speed_km/h': sum(speeds) / len(speeds),
                'Min_Speed_km/h': min(speeds),
                'Max_Speed_km/h': max(speeds),
            }
    
    return aggregates
