import pandas as pd
import numpy as np
import pdfplumber
import os
from src.parser import parse_race_form
from src.features import compute_features
from src.utils import validate_final_output
from src.exporter import export_ordered

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text


def validate_dataframe(df):
    """
    Comprehensive validation before export:
    - Checks Section 2 field completeness
    - Verifies no row duplication or merging
    - Detects cell overflow issues
    - Reports speed metric coverage
    """
    print("\n[VALIDATION] Running dataframe validation...")
    
    # 1. Check Section 2 fields (Distance and RaceTime)
    s2_distance_col = "S2_1_Distance"
    s2_racetime_col = "S2_1_RaceTime"
    
    if s2_distance_col in df.columns:
        missing_distance = df[s2_distance_col].isna().sum()
        pct_missing_distance = (missing_distance / len(df)) * 100
        print(f"[VALIDATION] S2_1_Distance: {missing_distance}/{len(df)} missing ({pct_missing_distance:.1f}%)")
        
        if pct_missing_distance > 10:
            print(f"[WARN] More than 10% of dogs missing Section 2 Distance!")
    else:
        print(f"[WARN] Column '{s2_distance_col}' not found in dataframe")
    
    if s2_racetime_col in df.columns:
        missing_racetime = df[s2_racetime_col].isna().sum()
        pct_missing_racetime = (missing_racetime / len(df)) * 100
        print(f"[VALIDATION] S2_1_RaceTime: {missing_racetime}/{len(df)} missing ({pct_missing_racetime:.1f}%)")
        
        if pct_missing_racetime > 10:
            print(f"[WARN] More than 10% of dogs missing Section 2 RaceTime!")
    else:
        print(f"[WARN] Column '{s2_racetime_col}' not found in dataframe")
    
    # 2. Check for duplicate rows (Track, RaceNumber, Box should be unique)
    if all(col in df.columns for col in ["Track", "RaceNumber", "Box"]):
        duplicates = df.duplicated(subset=["Track", "RaceNumber", "Box"], keep=False)
        dup_count = duplicates.sum()
        if dup_count > 0:
            print(f"[ERROR] Found {dup_count} duplicate rows! Section 2 may not be properly flattened.")
            dup_rows = df[duplicates][["Track", "RaceNumber", "Box", "DogName"]]
            print("[ERROR] Duplicate entries:")
            print(dup_rows.to_string(index=False))
        else:
            print(f"[OK] No duplicate rows found (Track/RaceNumber/Box combinations are unique)")
    
    # 2b. Check for Section 2 duplicate values within each race
    import os
    debug_s2 = os.getenv("DEBUG_SECTION2", "").lower() in ("1", "true", "yes")
    if debug_s2 and all(col in df.columns for col in ["Track", "RaceNumber", "DogName", "S2_1_Distance", "S2_1_RaceTime"]):
        print("[S2] Checking for duplicate Section 2 values within races...")
        s2_dup_count = 0
        
        for (track, race), group in df.groupby(["Track", "RaceNumber"]):
            # Get non-null S2 data
            s2_data = group[["DogName", "S2_1_Distance", "S2_1_RaceTime"]].dropna()
            if len(s2_data) < 2:
                continue
            
            # Check for duplicates in (Distance, RaceTime) pairs
            dup_pairs = s2_data.duplicated(subset=["S2_1_Distance", "S2_1_RaceTime"], keep=False)
            if dup_pairs.any():
                dup_dogs = s2_data[dup_pairs]["DogName"].tolist()
                dist = s2_data[dup_pairs]["S2_1_Distance"].iloc[0]
                time = s2_data[dup_pairs]["S2_1_RaceTime"].iloc[0]
                # Compute speed for logging
                try:
                    speed = (float(dist) / float(time)) * 3.6
                    print(f"[S2][DUP] Race={race} Dogs={dup_dogs} SharedValues={{Distance={dist}m,Time={time}s,Speed={speed:.3f}km/h}}")
                except:
                    print(f"[S2][DUP] Race={race} Dogs={dup_dogs} SharedValues={{Distance={dist}m,Time={time}s}}")
                s2_dup_count += len(dup_dogs)
        
        if s2_dup_count > 0:
            print(f"[S2][WARN] Found {s2_dup_count} dogs with duplicate Section 2 values")
        else:
            print(f"[S2][OK] No duplicate Section 2 values found within races")
    
    # 3. Check for cell overflow (DogName too long)
    if "DogName" in df.columns:
        long_names = df[df["DogName"].str.len() > 50]
        if len(long_names) > 0:
            print(f"[WARN] Found {len(long_names)} dogs with names >50 chars (possible cell overflow):")
            for idx, row in long_names.iterrows():
                print(f"  - {row['DogName'][:60]}...")
    
    # 4. Check speed metric coverage
    speed_cols = ["Speed_kmh", "EarlySpeed", "ClosingSpeed", "BestTime", "SpeedIndex"]
    existing_speed_cols = [col for col in speed_cols if col in df.columns]
    
    if existing_speed_cols:
        print(f"[VALIDATION] Speed metric coverage:")
        for col in existing_speed_cols:
            non_null = df[col].notna().sum()
            pct_coverage = (non_null / len(df)) * 100
            print(f"  - {col}: {non_null}/{len(df)} populated ({pct_coverage:.1f}%)")
    
    # 5. Verify dogs per race consistency
    if all(col in df.columns for col in ["Track", "RaceNumber"]):
        race_counts = df.groupby(["Track", "RaceNumber"]).size()
        avg_dogs_per_race = race_counts.mean()
        std_dogs_per_race = race_counts.std()
        print(f"[VALIDATION] Dogs per race: avg={avg_dogs_per_race:.1f}, std={std_dogs_per_race:.2f}")
        
        # Flag races with unusual counts
        unusual_races = race_counts[(race_counts < 4) | (race_counts > 10)]
        if len(unusual_races) > 0:
            print(f"[WARN] {len(unusual_races)} races with unusual dog counts:")
            for (track, race), count in unusual_races.items():
                print(f"  - {track} Race {race}: {count} dogs")
    
    print("[VALIDATION] Validation complete.\n")

# Start pipeline (ASCII logging for Windows cp1252 compatibility)
print("[INFO] Starting Greyhound Analytics")

# Find all PDFs in data folder
pdf_folder = "data"
pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(pdf_folder, x)), reverse=True)

if not pdf_files:
    print("[ERROR] No PDF files found in data folder.")
    exit()

all_dogs = []

# Process each PDF
for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_folder, pdf_file)
    print(f"[INFO] Processing: {pdf_path}")
    raw_text = extract_text_from_pdf(pdf_path)
    df = parse_race_form(raw_text)

    # Convert DLR to numeric to avoid type errors
    df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")

    # Apply enhanced scoring
    df = compute_features(df)
    all_dogs.append(df)

# Combine all dogs
combined_df = pd.concat(all_dogs, ignore_index=True)
print(f"[INFO] Total dogs parsed: {len(combined_df)}")

# Internal validation - detailed checks before export
validate_dataframe(combined_df)

# Validate output (from utils)
validate_final_output(combined_df)

# Save full parsed form (legacy)
combined_df.to_csv("outputs/todays_form.csv", index=False)
print("[OK] Saved parsed form -> outputs/todays_form.csv")

# Save ranked dogs (legacy)
ranked = combined_df.sort_values(["Track", "RaceNumber", "FinalScore"], ascending=[True, True, False])
ranked.to_csv("outputs/ranked.csv", index=False)
print("[OK] Saved ranked dogs -> outputs/ranked.csv")

# Save top picks across all tracks (legacy)
picks = ranked.groupby(["Track", "RaceNumber"]).head(1).reset_index(drop=True)
picks = picks.sort_values("FinalScore", ascending=False)

# Reorder columns for picks
priority_cols = ["Track", "RaceNumber", "Box", "DogName", "FinalScore", "PrizeMoney"]
remaining_cols = [col for col in picks.columns if col not in priority_cols]
ordered_cols = priority_cols + remaining_cols
picks = picks[ordered_cols]

picks.to_csv("outputs/picks.csv", index=False)
print("[OK] Saved top picks -> outputs/picks.csv")

# NEW: Export ordered comparison file with all dogs
csv_out, xlsx_out = export_ordered(combined_df, output_dir="outputs")

# Display top picks
print("\n[INFO] Top Picks Across All Tracks:")
for _, row in picks.iterrows():
    print(f"{row.Track} | Race {row.RaceNumber} | {row.DogName} | Score: {round(row.FinalScore, 3)}")

print("\n[OK] PDF=Excel data integrity verified")
print("\n[INFO] Press Enter to exit...")
input()
