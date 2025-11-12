from docx import Document

def read_docx_text(path: str) -> str:
    """Reads text content from a DOCX file."""
    doc = Document(path)
    text_parts = []
    for para in doc.paragraphs:
        text_parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text_parts.append(cell.text)
    return "\n".join(text_parts)
