"""
Main pipeline for DOCX to Excel/CSV extraction.
Clean rebuild - uses locked 58-column schema.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.read_docx_new import read_all_docx_files
from src.parse_docx_new import parse_all_files
from src.aggregate_history_new import aggregate_history
from src.export_to_excel_new import merge_summary_and_aggregates, export_to_excel_csv
from src.validation_and_audit_new import (
    create_audit_log, write_audit_logs, validate_data_quality, write_consistency_check
)


def main():
    """
    Main pipeline execution.
    """
    print("=" * 60)
    print(" GREYHOUND RACING DOCX → EXCEL/CSV PIPELINE")
    print("=" * 60)
    print()
    
    # Step 1: Read all DOCX files
    print("📄 Reading DOCX files from data/...")
    files_data = read_all_docx_files("data")
    
    if not files_data:
        print("❌ No DOCX files found in data/ directory")
        return
    
    print(f"✅ Read {len(files_data)} DOCX file(s)")
    for filename in files_data.keys():
        print(f"   - {filename}")
    print()
    
    # Step 2: Parse into summary and history rows
    print("🔍 Parsing DOCX content...")
    summary_rows, history_rows, unparsed = parse_all_files(files_data)
    
    print(f"✅ Extracted {len(summary_rows)} summary rows (dogs)")
    print(f"✅ Extracted {len(history_rows)} history rows")
    
    if unparsed:
        total_unparsed = sum(len(lines) for lines in unparsed.values())
        print(f"⚠️  {total_unparsed} unparsed lines (see logs for details)")
    print()
    
    # Step 3: Aggregate history to compute speed statistics
    print("📊 Aggregating historical data...")
    aggregates_df = aggregate_history(history_rows)
    
    if not aggregates_df.empty:
        print(f"✅ Computed speed statistics for {len(aggregates_df)} dogs")
    else:
        print("⚠️  No speed data computed (insufficient historical data)")
    print()
    
    # Step 4: Merge and export
    print("💾 Merging and exporting to Excel/CSV...")
    df_final, dup_count = merge_summary_and_aggregates(summary_rows, aggregates_df)
    
    export_stats = export_to_excel_csv(df_final)
    export_stats['duplicates_dropped'] = dup_count
    
    print(f"✅ Exported {export_stats['total_rows']} rows × {export_stats['columns']} columns")
    print(f"   Excel: {export_stats['excel_path']}")
    print(f"   CSV: {export_stats['csv_path']}")
    
    if dup_count > 0:
        print(f"   Dropped {dup_count} duplicate rows")
    print()
    
    # Step 5: Validation and audit logging
    print("📝 Writing audit logs and validation reports...")
    
    audit = create_audit_log(summary_rows, history_rows, unparsed, export_stats, df_final)
    write_audit_logs(audit, unparsed)
    
    validation = validate_data_quality(df_final)
    write_consistency_check(audit, validation)
    
    print()
    print("=" * 60)
    print("✅ Pipeline complete!")
    print("=" * 60)
    print()
    print("Output files:")
    print(f"  {export_stats['excel_path']}")
    print(f"  {export_stats['csv_path']}")
    print()
    print("Logs:")
    print("  outputs/logs/parse_audit.txt")
    print("  outputs/logs/validation_report.txt")
    print("  outputs/logs/consistency_check.txt")
    
    if unparsed:
        print("  outputs/logs/unparsed_lines.txt")
    
    print()


if __name__ == "__main__":
    main()
