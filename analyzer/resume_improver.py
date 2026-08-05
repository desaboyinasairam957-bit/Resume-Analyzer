"""
analyzer/resume_improver.py
Builds the improved-resume draft (text content) that gets rendered to PDF
by utils/pdf_generator.py.
"""

import re


def build_improved_resume_content(original_text, missing_keywords, suggestions):
    """Returns a dict of sections used by the PDF generator, keeping the
    content and the rendering (utils/pdf_generator.py) decoupled."""
    clean_suggestions = [re.sub(r"[*]", "", s) for s in suggestions]
    return {
        "heading": "Improved Resume Draft",
        "intro": (
            "This is an auto-generated improvement draft. Review and "
            "personalize before sending to employers."
        ),
        "missing_keywords": missing_keywords[:15],
        "suggestions": clean_suggestions,
        "original_text": original_text,
    }
