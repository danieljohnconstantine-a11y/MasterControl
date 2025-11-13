"""
Validation and Audit Module
Responsibility: Comprehensive logging, validation, and quality checks
"""
import json
import os
from datetime import datetime


def write_audit_log(docx_files, summary_rows, history_rows, unparsed_lines, export_stats, output_dir="outputs/logs"):
    """Write comprehensive audit log."""
    os.makedirs(output_dir, exist_ok=True)
    
    audit_path = os.path.join(output_dir, "parse_audit.txt")
    
    audit_data = {
        "timestamp": datetime.now().isoformat(),
        "docx_files_processed": len(docx_files),
        "docx_filenames": [f[0] for f in docx_files],
        "summary_rows_extracted": len(summary_rows),
        "history_rows_extracted": len(history_rows),
        "unparsed_lines_count": len(unparsed_lines),
        "total_rows_exported": export_stats.get("total_rows", 0),
        "duplicates_dropped": export_stats.get("duplicates_dropped", 0),
        "unique_tracks": export_stats.get("unique_tracks", 0),
        "unique_meetings": export_stats.get("unique_meetings", 0),
        "columns_exported": export_stats.get("columns_exported", 0),
        "dogs_with_speed_data": export_stats.get("dogs_with_speed_data", 0),
        "speed_data_percentage": round(
            (export_stats.get("dogs_with_speed_data", 0) / max(export_stats.get("total_rows", 1), 1)) * 100, 2
        ),
        "unparsed_sample": unparsed_lines[:50] if unparsed_lines else []
    }
    
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)
    
    return audit_path


def write_validation_report(summary_rows, output_dir="outputs/logs"):
    """Write data quality validation report."""
    os.makedirs(output_dir, exist_ok=True)
    
    report_path = os.path.join(output_dir, "validation_report.txt")
    
    # Analyze missing data by column
    from src.columns import COLUMN_ORDER
    
    total_rows = len(summary_rows)
    missing_analysis = {}
    
    for col in COLUMN_ORDER:
        empty_count = sum(1 for row in summary_rows if not str(row.get(col, "")).strip())
        missing_pct = (empty_count / max(total_rows, 1)) * 100
        missing_analysis[col] = {
            "empty_count": empty_count,
            "missing_percentage": round(missing_pct, 2)
        }
    
    # Sort by missing percentage
    sorted_missing = sorted(missing_analysis.items(), key=lambda x: x[1]["missing_percentage"], reverse=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_rows_analyzed": total_rows,
        "top_20_missing_columns": dict(sorted_missing[:20]),
        "data_quality_notes": [
            "Missing values are expected for fields not present in DOCX files",
            "No artificial defaults were added",
            "Empty strings indicate genuinely missing data"
        ]
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report_path


def write_consistency_check(summary_rows, docx_files, output_dir="outputs/logs"):
    """Write consistency check report with validation."""
    os.makedirs(output_dir, exist_ok=True)
    
    check_path = os.path.join(output_dir, "consistency_check.txt")
    
    # Required field validation
    required_fields = ["Track", "Race_Date", "Race_No", "Box", "Dog_Name"]
    nulls_in_required = {
        field: sum(1 for row in summary_rows if not str(row.get(field, "")).strip())
        for field in required_fields
    }
    
    # Speed data coverage
    total_dogs = len(summary_rows)
    dogs_with_speed = sum(1 for row in summary_rows if str(row.get("Avg_Speed_km/h", "")).strip())
    speed_pct = (dogs_with_speed / max(total_dogs, 1)) * 100
    
    # Checks
    checks = {
        "total_dogs_gt_zero": total_dogs > 0,
        "unique_tracks_ge_2": len(set(row.get("Track", "") for row in summary_rows)) >= 2,
        "speed_data_ge_20_pct": speed_pct >= 20,
        "no_nulls_in_required": all(count == 0 for count in nulls_in_required.values())
    }
    
    # Warnings
    warnings = []
    if not checks["speed_data_ge_20_pct"]:
        warnings.append(f"WARN: Speed data coverage = {speed_pct:.1f}%. Expected >= 20%.")
    
    status = "OK" if all(checks.values()) else "WARN"
    
    consistency_data = {
        "timestamp": datetime.now().isoformat(),
        "docx_files_processed": len(docx_files),
        "total_rows_exported": total_dogs,
        "unique_tracks": len(set(row.get("Track", "") for row in summary_rows)),
        "dogs_with_speed_data": dogs_with_speed,
        "speed_data_percentage": round(speed_pct, 2),
        "checks": checks,
        "warnings": warnings,
        "status": status
    }
    
    with open(check_path, "w", encoding="utf-8") as f:
        json.dump(consistency_data, f, indent=2, ensure_ascii=False)
    
    return check_path, status
