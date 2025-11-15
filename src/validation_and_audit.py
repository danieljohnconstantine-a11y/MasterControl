"""
Validation and audit logging for the pipeline.
"""
import os
import json
from datetime import datetime


def write_parse_audit(summary_count, history_count, unparsed_by_file, docx_count, output_dir='outputs/logs'):
    """Write parse audit log."""
    os.makedirs(output_dir, exist_ok=True)
    
    unparsed_counts = {k: len(v) for k, v in unparsed_by_file.items()}
    total_unparsed = sum(unparsed_counts.values())
    
    audit = {
        'timestamp': datetime.now().isoformat(),
        'docx_files_processed': docx_count,
        'summary_rows_extracted': summary_count,
        'history_rows_extracted': history_count,
        'total_rows_exported': summary_count,
        'columns_exported': 58,
        'unparsed_lines_by_file': unparsed_counts,
        'total_unparsed_lines': total_unparsed,
    }
    
    audit_path = os.path.join(output_dir, 'parse_audit.txt')
    with open(audit_path, 'w') as f:
        json.dump(audit, f, indent=2)
    
    print(f"✅ Parse audit written to {audit_path}")
    return audit


def write_validation_report(df, output_dir='outputs/logs'):
    """Write validation report."""
    os.makedirs(output_dir, exist_ok=True)
    
    if df.empty:
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_rows': 0,
            'message': 'No data extracted'
        }
    else:
        # Calculate missing rates
        missing_rates = {}
        for col in df.columns:
            empty_count = (df[col] == '').sum() + df[col].isna().sum()
            missing_rates[col] = round(empty_count / len(df) * 100, 2)
        
        # Sort by missing rate
        sorted_missing = dict(sorted(missing_rates.items(), key=lambda x: x[1], reverse=True)[:20])
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_rows': len(df),
            'top_20_missing_columns': sorted_missing,
            'unique_tracks': df['Track'].nunique(),
            'unique_dogs': df['Dog_Name'].nunique(),
        }
    
    report_path = os.path.join(output_dir, 'validation_report.txt')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Validation report written to {report_path}")
    return report


def write_consistency_check(df, docx_count, output_dir='outputs/logs'):
    """Write consistency check."""
    os.makedirs(output_dir, exist_ok=True)
    
    has_data = not df.empty
    has_track_info = has_data and (df['Track'] != '').any()
    has_dog_names = has_data and (df['Dog_Name'] != '').any()
    has_speed_data = has_data and (df['Avg_Speed_km/h'] != '').any()
    
    warnings = []
    if not has_data:
        warnings.append("WARN: No data extracted")
    if has_data and not has_speed_data:
        warnings.append("WARN: No dogs have speed data")
    
    status = "OK" if has_data and has_track_info and has_dog_names else "WARN"
    
    check = {
        'timestamp': datetime.now().isoformat(),
        'docx_files_processed': docx_count,
        'total_rows_exported': len(df),
        'unique_dogs': int(df['Dog_Name'].nunique()) if has_data else 0,
        'unique_tracks': int(df['Track'].nunique()) if has_data else 0,
        'checks': {
            'has_data': bool(has_data),
            'has_track_info': bool(has_track_info),
            'has_dog_names': bool(has_dog_names),
            'has_speed_data': bool(has_speed_data),
        },
        'warnings': warnings,
        'status': status,
    }
    
    check_path = os.path.join(output_dir, 'consistency_check.txt')
    with open(check_path, 'w') as f:
        json.dump(check, f, indent=2)
    
    print(f"✅ Consistency check written to {check_path}")
    return check


def write_unparsed_lines(unparsed_by_file, output_dir='outputs/logs'):
    """Write unparsed lines log."""
    os.makedirs(output_dir, exist_ok=True)
    
    log_path = os.path.join(output_dir, 'unparsed.txt')
    with open(log_path, 'w') as f:
        for filename, lines in unparsed_by_file.items():
            f.write(f"\n=== {filename} ===\n")
            for line in lines:
                f.write(f"{line}\n")
    
    total = sum(len(v) for v in unparsed_by_file.values())
    print(f"✅ Unparsed lines ({total} total) written to {log_path}")
