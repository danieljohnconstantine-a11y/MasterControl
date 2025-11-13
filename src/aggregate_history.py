"""
History Aggregation Module
Responsibility: Compute speed aggregates from historical race data
Formula: speed_km_h = (distance_m / time_seconds) * 3.6
"""
import re


def aggregate_history_per_dog(summary_rows, history_rows):
    """
    Compute Hist_Count, Avg_Speed_km/h, Min_Speed_km/h, Max_Speed_km/h for each dog.
    
    Args:
        summary_rows: List of dog summary dicts
        history_rows: List of historical race dicts
        
    Returns:
        Updated summary_rows with speed aggregates
    """
    # Group history by dog key
    history_by_dog = {}
    for hist in history_rows:
        key = (
            hist.get("Track", ""),
            hist.get("Race_Date", ""),
            hist.get("Race_No", ""),
            hist.get("Dog_Name", "")
        )
        if key not in history_by_dog:
            history_by_dog[key] = []
        history_by_dog[key].append(hist)
    
    # Compute aggregates for each summary row
    for dog in summary_rows:
        key = (
            dog.get("Track", ""),
            dog.get("Race_Date", ""),
            dog.get("Race_No", ""),
            dog.get("Dog_Name", "")
        )
        
        dog_histories = history_by_dog.get(key, [])
        
        # Compute speed for each history row
        speeds = []
        for hist in dog_histories:
            speed = compute_speed(hist.get("Hist_Distance", ""), hist.get("Hist_Race_Time", ""))
            if speed is not None:
                speeds.append(speed)
                hist["Hist_Speed_km/h"] = str(round(speed, 2))
        
        # Aggregate speeds
        dog["Hist_Count"] = str(len(dog_histories)) if dog_histories else ""
        
        if speeds:
            dog["Avg_Speed_km/h"] = str(round(sum(speeds) / len(speeds), 2))
            dog["Min_Speed_km/h"] = str(round(min(speeds), 2))
            dog["Max_Speed_km/h"] = str(round(max(speeds), 2))
        else:
            dog["Avg_Speed_km/h"] = ""
            dog["Min_Speed_km/h"] = ""
            dog["Max_Speed_km/h"] = ""
    
    return summary_rows


def compute_speed(distance_str, time_str):
    """
    Compute speed in km/h from distance (meters) and time.
    
    Args:
        distance_str: Distance as string (e.g., "450", "450m")
        time_str: Time as string (e.g., "25.50", "00:25.50", "25.50s")
        
    Returns:
        float: Speed in km/h, or None if computation fails
    """
    try:
        # Parse distance
        distance_match = re.search(r'(\d+)', str(distance_str))
        if not distance_match:
            return None
        distance_m = float(distance_match.group(1))
        
        # Parse time to seconds
        time_seconds = parse_time_to_seconds(time_str)
        if time_seconds is None or time_seconds <= 0:
            return None
        
        # Compute speed: (distance_m / time_seconds) * 3.6
        speed_kmh = (distance_m / time_seconds) * 3.6
        
        return speed_kmh
    except:
        return None


def parse_time_to_seconds(time_str):
    """
    Parse time string to seconds.
    Handles formats: "mm:ss.xx", "ss.xx", "ss"
    
    Args:
        time_str: Time string
        
    Returns:
        float: Time in seconds, or None if parsing fails
    """
    if not time_str:
        return None
    
    time_str = str(time_str).strip().replace("s", "").replace("S", "")
    
    try:
        # Format: mm:ss.xx or mm:ss
        if ":" in time_str:
            parts = time_str.split(":")
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        
        # Format: ss.xx or ss
        else:
            return float(time_str)
    except:
        return None
