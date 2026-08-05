"""
parser/preprocess.py
Cleans extracted resume text before it goes into the NLP pipeline.
"""

import re


def clean_text(text):
    """Collapses whitespace/newlines for downstream NLP; keep raw_text separately
    if you need line-based checks (e.g. quantified achievements)."""
    return re.sub(r"\s+", " ", text).strip()


def is_text_sufficient(text, min_words=20):
    return len(text.split()) >= min_words
