"""
Read DOCX files and extract all content as structured blocks.
No parsing - only extraction.
"""
from docx import Document
from typing import List, Dict, Any
import os


def extract_docx_content(docx_path: str) -> List[Dict[str, Any]]:
    """
    Extract all content from a DOCX file as structured blocks.
    
    Returns a list of blocks, each with:
    - type: "header" | "paragraph" | "table" | "footer"
    - text: list of text strings (for headers/footers/paragraphs)
    - table: list of lists (for tables)
    - raw: original text
    """
    blocks = []
    doc = Document(docx_path)
    
    # Extract header text
    for section in doc.sections:
        if section.header:
            header_text = []
            for para in section.header.paragraphs:
                if para.text.strip():
                    header_text.append(para.text.strip())
            if header_text:
                blocks.append({
                    "type": "header",
                    "text": header_text,
                    "raw": "\n".join(header_text)
                })
    
    # Extract paragraphs and tables in order
    for element in doc.element.body:
        # Check if it's a paragraph
        if element.tag.endswith('p'):
            for para in doc.paragraphs:
                if para._element == element:
                    text = para.text.strip()
                    if text:
                        blocks.append({
                            "type": "paragraph",
                            "text": [text],
                            "raw": text
                        })
                    break
        
        # Check if it's a table
        elif element.tag.endswith('tbl'):
            for table in doc.tables:
                if table._element == element:
                    table_data = []
                    for row in table.rows:
                        row_data = [cell.text.strip() for cell in row.cells]
                        table_data.append(row_data)
                    
                    if table_data:
                        blocks.append({
                            "type": "table",
                            "table": table_data,
                            "raw": "\n".join(["\t".join(row) for row in table_data])
                        })
                    break
    
    # Extract footer text
    for section in doc.sections:
        if section.footer:
            footer_text = []
            for para in section.footer.paragraphs:
                if para.text.strip():
                    footer_text.append(para.text.strip())
            if footer_text:
                blocks.append({
                    "type": "footer",
                    "text": footer_text,
                    "raw": "\n".join(footer_text)
                })
    
    return blocks


def read_all_docx_files(data_dir: str = "data") -> Dict[str, List[Dict[str, Any]]]:
    """
    Read all DOCX files from the data directory.
    
    Returns: dict mapping filename -> list of blocks
    """
    result = {}
    
    if not os.path.exists(data_dir):
        return result
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.docx') and not filename.startswith('~'):
            filepath = os.path.join(data_dir, filename)
            try:
                blocks = extract_docx_content(filepath)
                result[filename] = blocks
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return result
