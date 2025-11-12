# Greyhound Analytics Pipeline

Automated parsing and export of greyhound racing data from DOCX files.

## Features
- DOCX file ingestion
- Greyhound data parsing
- CSV and Excel export

## Requirements
Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
1. Place your `.docx` form files in the `data/` folder
2. Run `python main.py`
3. Check results in `outputs/`

## Output Files
- `greyhound_data.csv`: Parsed greyhound data in CSV format
- `greyhound_data.xlsx`: Parsed greyhound data in Excel format

## Project Structure
```
├── data/           # Input DOCX files
├── outputs/        # Generated CSV and Excel files
├── src/            # Source modules
│   ├── read_docx.py           # DOCX file reader
│   ├── parse_data.py          # Data parser
│   └── merge_sort_export.py   # Export handler
├── tests/          # Test files
├── main.py         # Main orchestrator
└── requirements.txt # Python dependencies
```
