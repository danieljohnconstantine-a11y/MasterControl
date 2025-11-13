"""
Main Pipeline Entry Point
Clean rebuild: 100% DOCX extraction with locked 58-column schema
"""
import os
from src.read_docx import read_all_docx_files
from src.parse_docx import parse_docx_blocks
from src.aggregate_history import aggregate_history_per_dog
from src.export_to_excel import export_to_excel_csv
from src.validation_and_audit import write_audit_log, write_validation_report, write_consistency_check

DATA_DIR = "data"
OUTPUT_DIR = "outputs"


def main():
    print("=" * 60)
    print(" GREYHOUND RACING DOCX → EXCEL/CSV PIPELINE")
    print(" Clean Rebuild - 100% Data Extraction")
    print("=" * 60)
    print()
    
    # Step 1: Read all DOCX files
    print("📄 Step 1: Reading DOCX files...")
    docx_files = read_all_docx_files(DATA_DIR)
    print(f"   Found {len(docx_files)} DOCX files")
    
    # Step 2: Parse blocks into summary and history rows
    print("\n🔍 Step 2: Parsing DOCX content...")
    all_summary_rows = []
    all_history_rows = []
    all_unparsed = []
    
    for filename, blocks in docx_files:
        print(f"   Processing: {filename}")
        summary_rows, history_rows, unparsed = parse_docx_blocks(blocks)
        all_summary_rows.extend(summary_rows)
        all_history_rows.extend(history_rows)
        all_unparsed.extend(unparsed)
        print(f"      → {len(summary_rows)} dogs, {len(history_rows)} history rows, {len(unparsed)} unparsed")
    
    print(f"\n   Total: {len(all_summary_rows)} summary rows, {len(all_history_rows)} history rows")
    if all_unparsed:
        print(f"   ⚠️  {len(all_unparsed)} unparsed lines (see audit log)")
    
    # Step 3: Aggregate history data
    print("\n⚡ Step 3: Computing speed aggregates...")
    all_summary_rows = aggregate_history_per_dog(all_summary_rows, all_history_rows)
    dogs_with_speed = sum(1 for row in all_summary_rows if row.get("Avg_Speed_km/h", ""))
    print(f"   Computed speeds for {dogs_with_speed} dogs")
    
    # Step 4: Export to Excel and CSV
    print("\n📊 Step 4: Exporting to Excel and CSV...")
    excel_path, csv_path, export_stats = export_to_excel_csv(all_summary_rows, OUTPUT_DIR)
    print(f"   ✓ Excel: {excel_path}")
    print(f"   ✓ CSV:   {csv_path}")
    print(f"   → {export_stats['total_rows']} rows (dropped {export_stats['duplicates_dropped']} duplicates)")
    print(f"   → {export_stats['columns_exported']} columns (locked schema)")
    
    # Step 5: Write audit and validation logs
    print("\n📝 Step 5: Writing audit and validation logs...")
    audit_path = write_audit_log(docx_files, all_summary_rows, all_history_rows, all_unparsed, export_stats)
    print(f"   ✓ Audit log: {audit_path}")
    
    validation_path = write_validation_report(all_summary_rows)
    print(f"   ✓ Validation report: {validation_path}")
    
    consistency_path, status = write_consistency_check(all_summary_rows, docx_files)
    print(f"   ✓ Consistency check: {consistency_path}")
    print(f"   → Status: {status}")
    
    print("\n" + "=" * 60)
    print("✅ Pipeline complete!")
    print(f"   Output files in: {OUTPUT_DIR}/")
    print(f"   Logs in: {OUTPUT_DIR}/logs/")
    print("=" * 60)


if __name__ == "__main__":
    main()
