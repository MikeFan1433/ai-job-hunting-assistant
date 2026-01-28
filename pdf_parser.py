"""PDF parsing utility for resume extraction."""
import pdfplumber
from typing import Optional
import io


def extract_text_from_pdf(pdf_file: bytes) -> str:
    """
    Extract text from PDF file.
    
    Args:
        pdf_file: PDF file content as bytes
        
    Returns:
        Extracted text as string
    """
    try:
        # Convert bytes to file-like object
        pdf_io = io.BytesIO(pdf_file)
        
        # Extract text using pdfplumber
        text_content = []
        with pdfplumber.open(pdf_io) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
        
        return "\n\n".join(text_content)
    
    except Exception as e:
        raise Exception(f"Error parsing PDF: {str(e)}")


def validate_pdf(pdf_file: bytes) -> tuple[bool, Optional[str]]:
    """
    Validate PDF file.
    
    Args:
        pdf_file: PDF file content as bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not pdf_file:
            return False, "PDF file is empty"
        
        if len(pdf_file) < 100:  # PDF header is usually at least 100 bytes
            return False, "PDF file is too small"
        
        # Check PDF magic bytes
        if not pdf_file.startswith(b'%PDF'):
            return False, "Invalid PDF format"
        
        # Try to open and read first page
        pdf_io = io.BytesIO(pdf_file)
        with pdfplumber.open(pdf_io) as pdf:
            if len(pdf.pages) == 0:
                return False, "PDF has no pages"
            
            # Try to extract text from first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            if not text or len(text.strip()) < 10:
                return False, "PDF appears to be empty or contains only images"
        
        return True, None
    
    except Exception as e:
        return False, f"PDF validation error: {str(e)}"
