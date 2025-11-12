import pandas as pd
import os
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
    """Derive Avg/Min/Max speed (km/h) from available race time & distance data."""
    import numpy as np
    
    speeds = []
    for _, row in df.iterrows():
        dist = row.get("Hist_Distance")
        t = row.get("Hist_Race_Time")
        try:
            dist_m = int(str(dist).strip().replace("m", ""))
            secs = _to_seconds(str(t))
            speed = (dist_m / secs) * 3.6 if secs > 0 else np.nan
        except Exception:
            speed = np.nan
        speeds.append(speed)
    df["Computed_Speed_km/h"] = speeds
    
    # Fill missing or empty speed fields with computed values
    for col in ["Avg_Speed_km/h", "Max_Speed_km/h", "Min_Speed_km/h"]:
        if col in df.columns:
            # Replace empty strings with NaN, then fill with computed speed
            df[col] = df[col].replace(["", None], np.nan)
            df[col] = df[col].fillna(df["Computed_Speed_km/h"])
    
    return df.drop(columns=["Computed_Speed_km/h"], errors="ignore")

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
