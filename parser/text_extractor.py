"""
parser/text_extractor.py
Turns the per-page text from pdf_parser into a single resume text string.
"""

from parser.pdf_parser import parse_pdf


def extract_text(file_obj):
    """Takes an uploaded file object, returns the full concatenated resume text."""
    pages = parse_pdf(file_obj)
    return "\n".join(pages)
