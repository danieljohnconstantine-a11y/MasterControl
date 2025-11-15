"""
Clean DOCX content extraction module.
Extracts all paragraphs from DOCX files without interpretation.
"""
import os
from docx import Document


def extract_docx(docx_path):
    """
    Extract all content from a DOCX file.
    
    Args:
        docx_path: Path to DOCX file
        
    Returns:
        dict with 'filename' and 'paragraphs' (list of text strings)
    """
    doc = Document(docx_path)
    filename = os.path.basename(docx_path)
    
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:  # Only include non-empty paragraphs
            paragraphs.append(text)
    
    return {
        'filename': filename,
        'paragraphs': paragraphs
    }


def read_all_docx(data_dir='data'):
    """
    Read all DOCX files from a directory.
    
    Args:
        data_dir: Directory containing DOCX files
        
    Returns:
        List of extraction results (one dict per file)
    """
    results = []
    
    if not os.path.exists(data_dir):
        return results
    
    for filename in sorted(os.listdir(data_dir)):
        if filename.endswith('.docx') and not filename.startswith('~'):
            docx_path = os.path.join(data_dir, filename)
            try:
                result = extract_docx(docx_path)
                results.append(result)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return results
