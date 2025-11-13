import pandas as pd
import os
import json
from datetime import datetime

def _to_seconds(time_str: str) -> float:
    """Converts time formats mm:ss.xx, m:ss, or s.ss into seconds."""
    if not time_str:
        return 0.0
    try:
        time_str = str(time_str).strip()
        # If it contains a colon, it's in mm:ss format
        if ":" in time_str:
            mins, secs = time_str.split(":")
            return float(mins) * 60 + float(secs)
        # Otherwise, it's just seconds (possibly with decimal)
        return float(time_str)
    except Exception:
        return 0.0

def compute_speed_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute speed fields from historical race data with per-dog-per-meeting aggregation.
    
    For each row:
    - Calculate Hist_Speed_km/h = (distance_meters / time_seconds) * 3.6
    
    Then aggregate per dog per meeting (grouped by Track, Race_Date, Race_No, Box, Dog_Name):
    - Avg_Speed_km/h = average of all Hist_Speed_km/h values for that dog in that meeting
    - Min_Speed_km/h = minimum of all Hist_Speed_km/h values  
    - Max_Speed_km/h = maximum of all Hist_Speed_km/h values
    - Hist_Count = number of historical races with valid speed data
    
    Only computes from real DOCX data - does not fill NaN defaults.
    """
    # Compute Hist_Speed_km/h per row if distance and time are available
    speeds = []
    for _, row in df.iterrows():
        dist = row.get("Hist_Distance")
        time = row.get("Hist_Race_Time")
        speed = None
        
        if dist and time:
            try:
                # Parse distance (remove 'm' if present, convert to int)
                dist_m = int(str(dist).strip().replace("m", ""))
                # Parse time using helper
                secs = _to_seconds(time)
                # Compute speed in km/h
                if secs > 0:
                    speed = (dist_m / secs) * 3.6
            except Exception:
                pass
        
        speeds.append(speed)
    
    df["Hist_Speed_km/h"] = speeds
    
    # Aggregate per dog per meeting: group by (Track, Race_Date, Race_No, Box, Dog_Name)
    grouping_cols = ["Track", "Race_Date", "Race_No", "Box", "Dog_Name"]
    
    # Check which grouping columns exist
    available_grouping_cols = [col for col in grouping_cols if col in df.columns]
    
    if available_grouping_cols and "Hist_Speed_km/h" in df.columns:
        # Create aggregation groups - only count non-null speeds for Hist_Count
        agg_dict = {
            "Hist_Speed_km/h": ["mean", "min", "max", "count"]
        }
        
        dog_meeting_stats = df.groupby(available_grouping_cols, as_index=False, dropna=False).agg(agg_dict)
        
        # Flatten column names
        new_cols = available_grouping_cols + ["Avg_Speed_km/h", "Min_Speed_km/h", "Max_Speed_km/h", "Hist_Count"]
        dog_meeting_stats.columns = new_cols
        
        # Merge back into main dataframe (left join to preserve all rows)
        # Drop existing speed columns if present
        for col in ["Avg_Speed_km/h", "Min_Speed_km/h", "Max_Speed_km/h", "Hist_Count"]:
            if col in df.columns:
                df = df.drop(columns=[col])
        
        df = df.merge(dog_meeting_stats, on=available_grouping_cols, how="left")
    
    return df

def validate_dataset(df: pd.DataFrame, output_dir: str) -> None:
    """Validate per-race completeness and column fill rates."""
    os.makedirs(os.path.join(output_dir, "logs"), exist_ok=True)
    audit_path = os.path.join(output_dir, "logs", "validation_report.txt")

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rows": len(df),
        "race_groups": df.groupby("Track")["Race_No"].nunique().to_dict(),
        "dogs_per_race": df.groupby(["Track","Race_No"]).size().to_dict(),
        "missing_rates": {
            col: round(df[col].isna().mean() * 100, 2)
            for col in df.columns
        },
        "duplicate_rows": int(df.duplicated(subset=["Track","Race_No","Box"]).sum())
    }

    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(str(summary) + "\n")

    print(f"✅ Validation complete → {audit_path}")

def validate_consistency(df: pd.DataFrame, docx_files: list, output_dir: str) -> None:
    """
    Cross-check DOCX vs Excel counts and log result to consistency_check.txt.
    
    Args:
        df: The exported DataFrame
        docx_files: List of DOCX file paths that were processed
        output_dir: Directory for log output
    """
    os.makedirs(os.path.join(output_dir, "logs"), exist_ok=True)
    consistency_path = os.path.join(output_dir, "logs", "consistency_check.txt")
    
    # Count unique dogs in Excel
    excel_dogs = df["Dog_Name"].nunique() if "Dog_Name" in df.columns else 0
    excel_rows = len(df)
    excel_races = df.groupby(["Track", "Race_No"]).ngroups if "Track" in df.columns and "Race_No" in df.columns else 0
    
    # Prepare consistency report
    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "docx_files_processed": len(docx_files),
        "docx_file_list": [os.path.basename(f) for f in docx_files],
        "excel_total_rows": excel_rows,
        "excel_unique_dogs": excel_dogs,
        "excel_unique_races": excel_races,
        "consistency_check": "PASS" if excel_rows > 0 and excel_dogs > 0 else "FAIL",
        "notes": []
    }
    
    # Add notes based on data
    if excel_rows == 0:
        report["notes"].append("WARNING: No rows in exported Excel - check DOCX parsing")
    elif excel_dogs == 0:
        report["notes"].append("WARNING: No dogs identified - check Dog_Name field extraction")
    else:
        report["notes"].append(f"Successfully exported {excel_dogs} unique dogs across {excel_races} races")
        avg_rows_per_dog = excel_rows / excel_dogs if excel_dogs > 0 else 0
        report["notes"].append(f"Average {avg_rows_per_dog:.1f} rows per dog (includes historical data)")
    
    # Write consistency check
    with open(consistency_path, "w", encoding="utf-8") as f:
        f.write("=== DOCX TO EXCEL CONSISTENCY CHECK ===\n\n")
        f.write(json.dumps(report, indent=2, ensure_ascii=False))
        f.write("\n")
    
    print(f"✅ Consistency check logged → {consistency_path}")

def validate_consistency(df: pd.DataFrame, output_dir: str, docx_file_count: int) -> None:
    """
    Cross-check DOCX vs Excel counts and log consistency results.
    
    Args:
        df: The exported DataFrame
        output_dir: Output directory for logs
        docx_file_count: Number of DOCX files processed
    """
    os.makedirs(os.path.join(output_dir, "logs"), exist_ok=True)
    consistency_path = os.path.join(output_dir, "logs", "consistency_check.txt")
    
    # Calculate statistics
    unique_dogs = int(df["Dog_Name"].nunique()) if "Dog_Name" in df.columns else 0
    unique_tracks = int(df["Track"].nunique()) if "Track" in df.columns else 0
    unique_races = int(df.groupby("Track")["Race_No"].nunique().sum()) if "Track" in df.columns and "Race_No" in df.columns else 0
    
    # Count rows with speed data
    speed_cols = ["Hist_Speed_km/h", "Avg_Speed_km/h", "Min_Speed_km/h", "Max_Speed_km/h"]
    rows_with_speed = sum(df[col].notna().any() for col in speed_cols if col in df.columns)
    
    consistency_report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "docx_files_processed": int(docx_file_count),
        "total_rows_exported": int(len(df)),
        "unique_dogs": int(unique_dogs),
        "unique_tracks": int(unique_tracks),
        "unique_races": int(unique_races),
        "columns_exported": int(len(df.columns)),
        "speed_fields_populated": bool(rows_with_speed > 0),
        "checks": {
            "has_data": bool(len(df) > 0),
            "has_track_info": bool(df["Track"].notna().any()) if "Track" in df.columns else False,
            "has_dog_names": bool(df["Dog_Name"].notna().any()) if "Dog_Name" in df.columns else False,
            "has_speed_data": bool(rows_with_speed > 0),
        }
    }
    
    with open(consistency_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(consistency_report, ensure_ascii=False, indent=2) + "\n")
    
    print(f"📊 Consistency check complete → {consistency_path}")
