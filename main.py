#!/usr/bin/env python3
"""
Main pipeline for DOCX to Excel/CSV extraction.
Canonical pipeline using modular architecture.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.read_docx import read_all_docx
from src.parse_docx import parse_all_docx
from src.aggregate_history import aggregate_history
from src.export_to_excel import merge_and_export
from src.validation_and_audit import (
    write_parse_audit,
    write_validation_report,
    write_consistency_check,
    write_unparsed_lines
)


def main():
    """Run the complete pipeline."""
    print("=" * 60)
    print("DOCX to Excel/CSV Pipeline - Canonical Architecture")
    print("=" * 60)
    
    # Step 1: Read all DOCX files
    print("\n📖 Step 1: Reading DOCX files...")
    extraction_results = read_all_docx('data')
    print(f"   Loaded {len(extraction_results)} DOCX files")
    
    # Step 2: Parse into summary and history rows
    print("\n🔍 Step 2: Parsing dog and history data...")
    summary_rows, history_rows, unparsed_by_file = parse_all_docx(extraction_results)
    print(f"   Extracted {len(summary_rows)} summary rows (dogs)")
    print(f"   Extracted {len(history_rows)} history rows")
    print(f"   Unparsed lines: {sum(len(v) for v in unparsed_by_file.values())}")
    
    # Step 3: Aggregate history data
    print("\n📊 Step 3: Aggregating speed statistics...")
    aggregates = aggregate_history(summary_rows, history_rows)
    dogs_with_speed = len(aggregates)
    print(f"   Computed speed stats for {dogs_with_speed} dogs")
    
    # Step 4: Export to Excel and CSV
    print("\n💾 Step 4: Exporting to Excel and CSV...")
    df = merge_and_export(summary_rows, aggregates)
    
    # Step 5: Generate validation and audit logs
    print("\n📝 Step 5: Generating validation and audit logs...")
    write_parse_audit(len(summary_rows), len(history_rows), unparsed_by_file, len(extraction_results))
    write_validation_report(df)
    write_consistency_check(df, len(extraction_results))
    write_unparsed_lines(unparsed_by_file)
    
    print("\n" + "=" * 60)
    print("✅ Pipeline complete!")
    print("=" * 60)
    print(f"\n📁 Outputs:")
    print(f"   - outputs/all_dogs_master.xlsx ({len(df)} rows)")
    print(f"   - outputs/all_dogs_master.csv")
    print(f"   - outputs/logs/parse_audit.txt")
    print(f"   - outputs/logs/validation_report.txt")
    print(f"   - outputs/logs/consistency_check.txt")
    print(f"   - outputs/logs/unparsed.txt")
    print()


if __name__ == '__main__':
    main()
