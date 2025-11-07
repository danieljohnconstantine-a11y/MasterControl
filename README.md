# MasterControl - PDF to Excel Converter

A simple Python tool to convert PDF files containing tables to Excel format.

## Features

- Extract tables from PDF files
- Convert to Excel (.xlsx) format
- Support for multiple tables (each table in a separate sheet)
- Handle both bordered and borderless tables
- Command-line interface for easy usage

## Installation

```bash
pip install -r requirements.txt
```

**Note:** `tabula-py` requires Java to be installed on your system. Install Java if you don't have it:
- On Ubuntu/Debian: `sudo apt-get install default-jre`
- On macOS: `brew install openjdk`
- On Windows: Download from [java.com](https://www.java.com)

## Usage

### Basic Usage

```bash
python pdf_to_excel.py input.pdf
```

This will create `input.xlsx` in the same directory.

### Specify Output File

```bash
python pdf_to_excel.py input.pdf -o output.xlsx
```

### Extract Specific Pages

```bash
# Extract from a single page
python pdf_to_excel.py input.pdf --pages 1

# Extract from a range of pages
python pdf_to_excel.py input.pdf --pages 1-3

# Extract all pages (default)
python pdf_to_excel.py input.pdf --pages all
```

## Requirements

- Python 3.7+
- Java Runtime Environment (JRE)
- Dependencies listed in `requirements.txt`

## How It Works

The tool uses:
- **tabula-py**: To extract tables from PDF files
- **pandas**: To process and organize the data
- **openpyxl**: To write Excel files

## Limitations

- Only extracts tabular data (tables) from PDFs
- Works best with well-structured PDFs
- Requires Java to be installed
- May not preserve complex formatting
