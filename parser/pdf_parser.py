"""
parser/pdf_parser.py
Reads a PDF file object and returns raw page-level text.
PDFPlumber is tried first (better layout-aware extraction); PyPDF2 is used
as an automatic fallback if PDFPlumber fails or returns nothing.
"""

import pdfplumber
from PyPDF2 import PdfReader


def read_pdf_pdfplumber(file_obj):
    file_obj.seek(0)
    pages_text = []
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")
    return pages_text


def read_pdf_pypdf2(file_obj):
    file_obj.seek(0)
    reader = PdfReader(file_obj)
    return [page.extract_text() or "" for page in reader.pages]


def parse_pdf(file_obj):
    """Returns list of per-page text strings. Tries PDFPlumber, falls back to PyPDF2."""
    try:
        pages = read_pdf_pdfplumber(file_obj)
        if any(p.strip() for p in pages):
            return pages
    except Exception:
        pass

    try:
        return read_pdf_pypdf2(file_obj)
    except Exception:
        return []
