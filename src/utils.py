# src/utils.py - Utility functions
import os

def setup_environment():
    """Setup and validate environment"""
    print("[INFO] Setting up environment...")
    
    # Ensure outputs directory exists
    from config import OUTPUT_DIR
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[OK] Created outputs directory: {OUTPUT_DIR}")
    else:
        print(f"[OK] Outputs directory exists: {OUTPUT_DIR}")
    
    return True

def find_pdf_files():
    """Find all PDF files in data directory"""
    from config import PDF_DIR
    
    if os.path.exists(PDF_DIR):
        pdf_files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
        if pdf_files:
            print(f"[INFO] Found {len(pdf_files)} PDF files")
            return pdf_files
        else:
            print("[ERROR] No PDF files found in data folder!")
    else:
        print("[ERROR] Data folder not found!")
    
    return []


def validate_final_output(df):
    """
    Validate the final output DataFrame before export.
    Checks for required columns, duplicates, and data coverage.
    
    Args:
        df: Final DataFrame to validate
    """
    required = ["Track", "RaceNumber", "Box", "DogName"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[WARN] Missing columns: {missing}")

    dups = df.duplicated(subset=["Track", "RaceNumber", "Box"], keep=False)
    if dups.any():
        print(f"[WARN] Found {dups.sum()} duplicate rows (Section 2 not flattened).")

    speed_cols = [c for c in df.columns if c.startswith(("Speed", "Split", "BestTime", "S2_"))]
    if speed_cols:
        coverage = {c: round(df[c].notna().mean() * 100, 1) for c in speed_cols[:10]}  # First 10 for brevity
        print(f"[INFO] Speed coverage (% non-null): {coverage}")
    
    print(f"[OK] Validation complete: {len(df)} rows x {len(df.columns)} columns")
