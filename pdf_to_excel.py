#!/usr/bin/env python3
"""
PDF to Excel Converter
Converts PDF files containing tables to Excel format.
"""

import argparse
import sys
from pathlib import Path
import tabula
import pandas as pd


def convert_pdf_to_excel(pdf_path, output_path=None, pages='all'):
    """
    Convert PDF file to Excel format.
    
    Args:
        pdf_path (str): Path to the input PDF file
        output_path (str, optional): Path to the output Excel file. 
                                     If None, uses the same name as PDF with .xlsx extension
        pages (str or int): Pages to extract. Default is 'all'
    
    Returns:
        str: Path to the created Excel file
    """
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_file.suffix.lower() == '.pdf':
        raise ValueError(f"Input file must be a PDF: {pdf_path}")
    
    # Determine output path
    if output_path is None:
        output_path = pdf_file.with_suffix('.xlsx')
    else:
        output_path = Path(output_path)
    
    # Extract tables from PDF
    try:
        tables = tabula.read_pdf(
            str(pdf_file),
            pages=pages,
            multiple_tables=True,
            lattice=True  # Better for tables with clear borders
        )
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}", file=sys.stderr)
        print("Trying alternative extraction method...", file=sys.stderr)
        try:
            tables = tabula.read_pdf(
                str(pdf_file),
                pages=pages,
                multiple_tables=True,
                stream=True  # Better for tables without clear borders
            )
        except Exception as e2:
            raise RuntimeError(f"Failed to extract tables from PDF: {e2}")
    
    if not tables:
        raise ValueError("No tables found in the PDF file")
    
    # Write tables to Excel
    with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
        for i, table in enumerate(tables):
            sheet_name = f'Table_{i+1}' if len(tables) > 1 else 'Data'
            table.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return str(output_path)


def main():
    """Main function to handle command-line interface."""
    parser = argparse.ArgumentParser(
        description='Convert PDF files to Excel format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.pdf
  %(prog)s input.pdf -o output.xlsx
  %(prog)s input.pdf --pages 1-3
  %(prog)s input.pdf --pages all
        """
    )
    
    parser.add_argument('pdf_file', help='Input PDF file path')
    parser.add_argument(
        '-o', '--output',
        help='Output Excel file path (default: same name as PDF with .xlsx extension)'
    )
    parser.add_argument(
        '--pages',
        default='all',
        help='Pages to extract (default: all). Examples: "1", "1-3", "all"'
    )
    
    args = parser.parse_args()
    
    try:
        output_file = convert_pdf_to_excel(
            args.pdf_file,
            args.output,
            args.pages
        )
        print(f"✓ Successfully converted PDF to Excel: {output_file}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
