import pandas as pd
import os

def merge_sort_and_export(records, output_dir):
    """Combine records, sort by Track→Race_No→Box, and export to Excel/CSV."""
    if not records:
        print("⚠️ No records found to export.")
        return

    df = pd.DataFrame(records)
    sort_cols = ["Track", "Race_No", "Box"]
    df = df.sort_values(by=sort_cols, ascending=[True, True, True])

    os.makedirs(output_dir, exist_ok=True)
    excel_path = os.path.join(output_dir, "all_dogs_master.xlsx")
    csv_path = os.path.join(output_dir, "all_dogs_master.csv")

    df.to_excel(excel_path, index=False, engine="openpyxl")
    df.to_csv(csv_path, index=False)

    print(f"✅ Exported {len(df)} records:")
    print(f"   📊 Excel: {excel_path}")
    print(f"   📄 CSV:   {csv_path}")
