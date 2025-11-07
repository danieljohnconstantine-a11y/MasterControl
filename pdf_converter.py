"""
PDF to Text Converter

This module handles conversion of PDF files to text.
"""

import os
from typing import Dict
from PyPDF2 import PdfReader


class PDFConverter:
    """Convert PDF files to text."""
    
    def __init__(self):
        pass
    
    def convert_pdf_to_text(self, pdf_path: str, output_path: str = None) -> str:
        """
        Convert a PDF file to text.
        
        Args:
            pdf_path: Path to the PDF file
            output_path: Optional path to save the text file
            
        Returns:
            Extracted text content
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Read PDF
        reader = PdfReader(pdf_path)
        text_content = []
        
        # Extract text from all pages
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        
        full_text = '\n'.join(text_content)
        
        # Save to file if output path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
        
        return full_text
    
    def convert_all_pdfs_in_directory(self, directory: str, output_dir: str = None) -> Dict[str, str]:
        """
        Convert all PDF files in a directory to text.
        
        Args:
            directory: Directory containing PDF files
            output_dir: Optional directory to save text files
            
        Returns:
            Dictionary mapping PDF filenames to extracted text
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        results = {}
        
        for filename in os.listdir(directory):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(directory, filename)
                
                output_path = None
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    txt_filename = filename[:-4] + '.txt'
                    output_path = os.path.join(output_dir, txt_filename)
                
                text = self.convert_pdf_to_text(pdf_path, output_path)
                results[filename] = text
        
        return results
