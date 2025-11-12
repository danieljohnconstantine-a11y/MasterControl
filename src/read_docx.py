"""
Module for reading text content from DOCX files.
"""
from docx import Document


def read_docx_text(filepath):
    """
    Extract all text from a DOCX file.
    
    Args:
        filepath (str): Path to the DOCX file
        
    Returns:
        str: Extracted text content from the DOCX file
    """
    doc = Document(filepath)
    full_text = []
    
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    
    return '\n'.join(full_text)
