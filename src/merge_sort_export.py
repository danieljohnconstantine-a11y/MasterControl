import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict
from .columns import COLUMN_ORDER

def _coerce_int(series):
    try:
        return pd.to_numeric(series, errors="coerce")
    except Exception:
        return series

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Add any missing columns as empty strings
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = ""
    # Keep any extra columns at the end (but we still export ordered)
    return df

def _ordered(df: pd.DataFrame) -> pd.DataFrame:
    cols_in_df = [c for c in COLUMN_ORDER if c in df.columns]
    extras = [c for c in df.columns if c not in COLUMN_ORDER]
    return df[cols_in_df + extras]

def _audit(df: pd.DataFrame, output_dir: str, notes: List[str]) -> None:
    os.makedirs(os.path.join(output_dir, "logs"), exist_ok=True)
    audit_path = os.path.join(output_dir, "logs", "parse_audit.txt")
    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rows": int(len(df)),
        "missing_columns": [c for c in COLUMN_ORDER if c not in df.columns],
        "notes": notes,
        "samples": df.head(5).to_dict(orient="records"),
    }
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(f"📝 Audit written → {audit_path}")

def merge_sort_and_export(records: List[Dict], output_dir: str) -> None:
    if not records:
        print("⚠️ No records found to export.")
        _audit(pd.DataFrame(), output_dir, ["No records"])
        return

    df = pd.DataFrame(records)
    df = _ensure_columns(df)

    # Sort by Track, Race_No, Box (numeric if possible for race/box)
    # Preserve original values in export while sorting on numeric views
    df["_Race_No_num"] = _coerce_int(df["Race_No"])
    df["_Box_num"] = _coerce_int(df["Box"])
    df = df.sort_values(by=["Track", "_Race_No_num", "_Box_num", "Race_No", "Box"], ascending=[True, True, True, True, True])
    df = df.drop(columns=["_Race_No_num", "_Box_num"])

    # Enforce column order for export
    df_out = _ordered(df)

    os.makedirs(output_dir, exist_ok=True)
    excel_path = os.path.join(output_dir, "all_dogs_master.xlsx")
    csv_path = os.path.join(output_dir, "all_dogs_master.csv")
    df_out.to_excel(excel_path, index=False)
    df_out.to_csv(csv_path, index=False, encoding="utf-8-sig")

    notes = [
        f"Exported columns={len(df_out.columns)} (ordered first {len(COLUMN_ORDER)}).",
        "Sorted by Track → Race_No → Box.",
    ]
    _audit(df_out, output_dir, notes)
    print(f"✅ Exported {len(df_out)} rows → {excel_path}, {csv_path}")
