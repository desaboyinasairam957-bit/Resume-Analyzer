"""
utils/file_handler.py
Handles saving uploaded resumes to uploads/ and generated files to output/.
Keeping I/O in one place makes it easy to swap in S3 / cloud storage later.
"""

import os
import time

from config import UPLOAD_DIR, OUTPUT_DIR, GENERATED_RESUME_DIR, ensure_directories


def save_uploaded_resume(uploaded_file):
    """Saves the uploaded file bytes to uploads/ with a timestamped name.
    Returns the saved path. Safe to call even if the caller doesn't need
    the file kept - it's useful for audit/history features later."""
    ensure_directories()
    uploaded_file.seek(0)
    timestamp = int(time.time())
    safe_name = f"{timestamp}_{uploaded_file.name}"
    path = os.path.join(UPLOAD_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(uploaded_file.read())
    uploaded_file.seek(0)
    return path


def save_output_text(filename, content):
    ensure_directories()
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generated_resume_path(filename="improved_resume.pdf"):
    ensure_directories()
    return os.path.join(GENERATED_RESUME_DIR, filename)
