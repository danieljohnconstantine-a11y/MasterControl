import os
import pdfplumber

def extract_text_from_latest_pdf(folder):
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return None

    pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("❌ No PDF files found in folder.")
        return None

    # Sort by most recently modified
    pdf_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
    pdf_path = os.path.join(folder, pdf_files[0])

    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"⚠️ Error reading PDF: {e}")
        return None

    print(f"✅ Extracted text from {os.path.basename(pdf_path)}")
    return text
