"""
Validation and audit logging.
"""
import json
import os
from datetime import datetime
from typing import Dict, List
import pandas as pd
import numpy as np


def convert_to_serializable(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    return obj


def create_audit_log(summary_rows: List[Dict], history_rows: List[Dict], 
                     unparsed: Dict, export_stats: Dict, df_final: pd.DataFrame) -> Dict:
    """
    Create comprehensive audit log.
    """
    audit = {
        'timestamp': datetime.now().isoformat(),
        'docx_files_processed': len(unparsed) if unparsed else 0,
        'summary_rows_extracted': len(summary_rows),
        'history_rows_extracted': len(history_rows),
        'total_rows_exported': export_stats.get('total_rows', 0),
        'columns_exported': export_stats.get('columns', 0),
        'duplicates_dropped': export_stats.get('duplicates_dropped', 0),
    }
    
    # Compute unique counts
    if not df_final.empty:
        audit['unique_tracks'] = df_final['Track'].nunique()
        audit['unique_dogs'] = df_final['Dog_Name'].nunique()
        audit['unique_meetings'] = df_final.groupby(['Track', 'Race_Date']).ngroups
        
        # Speed data coverage
        speed_cols = ['Avg_Speed_km/h', 'Min_Speed_km/h', 'Max_Speed_km/h']
        dogs_with_speed = df_final[speed_cols].notna().any(axis=1).sum()
        audit['dogs_with_speed_data'] = int(dogs_with_speed)
        audit['speed_data_percentage'] = round(100 * dogs_with_speed / len(df_final), 2) if len(df_final) > 0 else 0
        
        # Top tracks
        track_counts = df_final['Track'].value_counts().head(5)
        audit['top_5_tracks_by_dog_count'] = [
            {'track': track, 'dog_count': int(count)} 
            for track, count in track_counts.items()
        ]
    
    # Unparsed lines
    audit['unparsed_lines_by_file'] = {
        filename: len(lines) for filename, lines in unparsed.items()
    }
    
    audit['notes'] = [
        f"Dropped {export_stats.get('duplicates_dropped', 0)} duplicate rows on (Track, Race_Date, Race_No, Box, Dog_Name).",
        "Sorted strictly by Track → Race_Date (as date) → Race_No (numeric) → Box (numeric).",
        f"Final locked schema with {export_stats.get('columns', 0)} columns including metadata fields."
    ]
    
    return audit


def write_audit_logs(audit: Dict, unparsed: Dict, output_dir: str = "outputs/logs"):
    """
    Write audit logs to files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Write parse audit
    audit_path = os.path.join(output_dir, "parse_audit.txt")
    with open(audit_path, 'w') as f:
        # Convert numpy types to native Python types
        serializable_audit = convert_to_serializable(audit)
        json.dump(serializable_audit, f, indent=2)
    
    # Write unparsed lines
    if unparsed:
        unparsed_path = os.path.join(output_dir, "unparsed_lines.txt")
        with open(unparsed_path, 'w') as f:
            for filename, lines in unparsed.items():
                f.write(f"\n=== {filename} ===\n")
                for line in lines:
                    f.write(f"{line}\n")
    
    print(f"✅ Audit logs written to {output_dir}")


def validate_data_quality(df: pd.DataFrame, output_dir: str = "outputs/logs") -> Dict:
    """
    Validate data quality and write validation report.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    validation = {
        'timestamp': datetime.now().isoformat(),
        'total_rows': len(df),
        'total_columns': len(df.columns),
    }
    
    # Required field checks
    required_fields = ['Track', 'Race_Date', 'Race_No', 'Box', 'Dog_Name']
    validation['required_field_checks'] = {}
    
    for field in required_fields:
        null_count = df[field].isna().sum()
        validation['required_field_checks'][field] = {
            'null_count': int(null_count),
            'null_percentage': round(100 * null_count / len(df), 2) if len(df) > 0 else 0
        }
    
    # Missing data analysis
    missing_rates = df.isna().sum() / len(df) * 100
    top_missing = missing_rates.sort_values(ascending=False).head(20)
    
    validation['top_20_missing_columns'] = {
        col: round(rate, 2) for col, rate in top_missing.items()
    }
    
    # Write validation report
    report_path = os.path.join(output_dir, "validation_report.txt")
    with open(report_path, 'w') as f:
        json.dump(validation, f, indent=2)
    
    print(f"✅ Validation report written to {report_path}")
    
    return validation


def write_consistency_check(audit: Dict, validation: Dict, output_dir: str = "outputs/logs"):
    """
    Write consistency check combining audit and validation data.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    consistency = {
        'timestamp': datetime.now().isoformat(),
        'docx_files_processed': audit.get('docx_files_processed', 0),
        'total_rows_exported': audit.get('total_rows_exported', 0),
        'unique_dogs': audit.get('unique_dogs', 0),
        'unique_tracks': audit.get('unique_tracks', 0),
        'unique_meetings': audit.get('unique_meetings', 0),
        'columns_exported': audit.get('columns_exported', 0),
        'speed_fields_populated': audit.get('dogs_with_speed_data', 0) > 0,
        'checks': {
            'has_data': audit.get('total_rows_exported', 0) > 0,
            'has_track_info': audit.get('unique_tracks', 0) > 0,
            'has_dog_names': audit.get('unique_dogs', 0) > 0,
            'has_speed_data': audit.get('dogs_with_speed_data', 0) > 0,
        }
    }
    
    # Add warnings if any
    warnings = []
    
    if audit.get('dogs_with_speed_data', 0) == 0:
        warnings.append("WARN: No dogs have speed data")
    elif audit.get('speed_data_percentage', 0) < 20:
        warnings.append(f"WARN: Speed data coverage = {audit.get('speed_data_percentage', 0)}%. Expected >= 20%.")
    
    if warnings:
        consistency['warnings'] = warnings
        consistency['status'] = 'WARN'
    else:
        consistency['status'] = 'OK'
    
    consistency_path = os.path.join(output_dir, "consistency_check.txt")
    with open(consistency_path, 'w') as f:
        json.dump(consistency, f, indent=2)
    
    print(f"✅ Consistency check written to {consistency_path}")
    print(f"Status: {consistency['status']}")
