import os
from tqdm import tqdm
from src.read_docx import read_docx_text
from src.parse_data import parse_greyhound_data
from src.merge_sort_export import merge_sort_and_export

DATA_DIR = "data"
OUTPUT_DIR = "outputs"

def main():
    all_summary_rows = []
    all_history_rows = []
    docx_files = []
    for file in tqdm(os.listdir(DATA_DIR), desc="Processing DOCX files"):
        if file.lower().endswith(".docx"):
            path = os.path.join(DATA_DIR, file)
            docx_files.append(path)
            text = read_docx_text(path)
            summary_rows, history_rows = parse_greyhound_data(text)
            all_summary_rows.extend(summary_rows)
            all_history_rows.extend(history_rows)

    merge_sort_and_export(all_summary_rows, all_history_rows, OUTPUT_DIR, docx_files)

if __name__ == "__main__":
    main()
