"""
utils/helper.py
Small shared helpers: contact info regex extraction, experience estimates.
"""

import re


def extract_contact_info(text):
    email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    phone = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", text)
    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
    }
