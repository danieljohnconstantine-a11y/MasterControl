"""
DOCX Content Extraction Module
Responsibility: Extract ALL content from DOCX files without interpretation
Returns structured blocks for downstream parsing
"""
from docx import Document
import os


def extract_docx_content(docx_path):
    """
    Extract all content from a DOCX file into structured blocks.
    
    Args:
        docx_path: Path to the DOCX file
        
    Returns:
        List of dicts with structure:
        {
            "type": "header" | "paragraph" | "table" | "footer",
            "text": str or list of strings,
            "table": list of lists (for table type),
            "source_file": filename
        }
    """
    doc = Document(docx_path)
    blocks = []
    filename = os.path.basename(docx_path)
    
    # Extract headers
    for section in doc.sections:
        header = section.header
        if header and header.paragraphs:
            header_texts = [p.text.strip() for p in header.paragraphs if p.text.strip()]
            if header_texts:
                blocks.append({
                    "type": "header",
                    "text": header_texts,
                    "source_file": filename
                })
    
    # Extract paragraphs and tables in order
    for element in doc.element.body:
        # Check if it's a paragraph
        if element.tag.endswith('p'):
            # Find the paragraph object
            for p in doc.paragraphs:
                if p._element == element:
                    text = p.text.strip()
                    if text:
                        blocks.append({
                            "type": "paragraph",
                            "text": text,
                            "source_file": filename
                        })
                    break
        
        # Check if it's a table
        elif element.tag.endswith('tbl'):
            # Find the table object
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
                            "text": None,
                            "source_file": filename
                        })
                    break
    
    # Extract footers
    for section in doc.sections:
        footer = section.footer
        if footer and footer.paragraphs:
            footer_texts = [p.text.strip() for p in footer.paragraphs if p.text.strip()]
            if footer_texts:
                blocks.append({
                    "type": "footer",
                    "text": footer_texts,
                    "source_file": filename
                })
    
    return blocks


def read_all_docx_files(data_dir="data"):
    """
    Read all DOCX files from a directory.
    
    Args:
        data_dir: Directory containing DOCX files
        
    Returns:
        List of tuples: (filename, blocks)
    """
    docx_files = []
    
    if not os.path.exists(data_dir):
        return docx_files
    
    for filename in os.listdir(data_dir):
        if filename.lower().endswith('.docx') and not filename.startswith('~'):
            filepath = os.path.join(data_dir, filename)
            try:
                blocks = extract_docx_content(filepath)
                docx_files.append((filename, blocks))
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return docx_files
