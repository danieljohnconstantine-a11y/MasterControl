# src/utils.py - Utility functions
import os

def setup_environment():
    """Setup and validate environment"""
    print("🔧 Setting up environment...")
    
    # Ensure outputs directory exists
    from config import OUTPUT_DIR
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"✅ Created outputs directory: {OUTPUT_DIR}")
    else:
        print(f"✅ Outputs directory exists: {OUTPUT_DIR}")
    
    return True

def find_pdf_files():
    """Find all PDF files in data directory"""
    from config import PDF_DIR
    
    if os.path.exists(PDF_DIR):
        pdf_files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
        if pdf_files:
            print(f"📁 Found {len(pdf_files)} PDF files")
            return pdf_files
        else:
            print("❌ No PDF files found in data folder!")
    else:
        print("❌ Data folder not found!")
    
    return []