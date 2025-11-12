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
    """
    NO-OP function - speed fields are NOT computed or filled.
    
    Previously computed Avg/Min/Max speed fields from race time & distance data.
    Now disabled to preserve only authentic DOCX values per Phase 6 requirements.
    
    Only real values from DOCX are preserved. This function is kept for 
    backward compatibility but does nothing.
    """
    # Return dataframe unchanged - no artificial data generation
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
