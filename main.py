import os
from tqdm import tqdm
from src.read_docx import read_docx_text
from src.parse_data import parse_greyhound_data
from src.merge_sort_export import merge_sort_and_export

DATA_DIR = "data"
OUTPUT_DIR = "outputs"

def main():
    all_records = []
    for file in tqdm(os.listdir(DATA_DIR), desc="Processing DOCX files"):
        if file.lower().endswith(".docx"):
            path = os.path.join(DATA_DIR, file)
            text = read_docx_text(path)
            dogs = parse_greyhound_data(text)
            all_records.extend(dogs)

    merge_sort_and_export(all_records, OUTPUT_DIR)

if __name__ == "__main__":
    main()
