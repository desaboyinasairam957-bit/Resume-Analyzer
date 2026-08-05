"""
analyzer/ats_score.py
Computes the 0-100 ATS-compatibility score and its component breakdown.
"""

import re

from config import ATS_WEIGHTS_NO_JD, ATS_WEIGHTS_WITH_JD
from utils.helper import extract_contact_info


def check_sections(text):
    text_lower = text.lower()
    return {
        "Contact Info": "@" in text_lower,
        "Summary/Objective": any(k in text_lower for k in ["summary", "objective", "profile"]),
        "Experience": any(k in text_lower for k in ["experience", "employment", "work history"]),
        "Education": any(k in text_lower for k in ["education", "degree", "university", "college"]),
        "Skills": any(k in text_lower for k in ["skills", "technologies", "competencies"]),
        "Projects": "project" in text_lower,
    }


def check_quantified_achievements(raw_text):
    lines = raw_text.split("\n")
    quantified = []
    for line in lines:
        if re.search(r"\d+%|\$\d+|\d+x\b|\d+\+|\bincreased\b|\bdecreased\b|\breduced\b", line, re.I):
            if re.search(r"\d", line):
                quantified.append(line.strip())
    return quantified


def calculate_ats_score(text, found_skills, sections, action_verbs, quantified, jd_keywords=None):
    """
    When jd_keywords is provided, the score is computed directly against
    that job description - the JD-match component dominates the weighting
    (ATS_WEIGHTS_WITH_JD), so this becomes a job-specific score rather than
    a generic resume-quality score. Without a JD, ATS_WEIGHTS_NO_JD applies
    and jd_match is skipped entirely.
    """
    weights = ATS_WEIGHTS_WITH_JD if jd_keywords else ATS_WEIGHTS_NO_JD
    score = 0
    breakdown = {}

    section_score = round(sum(sections.values()) / len(sections) * weights["sections"])
    breakdown["Section completeness"] = section_score
    score += section_score

    total_skills = sum(len(v) for v in found_skills.values())
    skill_score = min(weights["skills"], total_skills * 2)
    breakdown["Skills coverage"] = skill_score
    score += skill_score

    verb_score = min(weights["action_verbs"], len(action_verbs) * 2)
    breakdown["Strong action verbs"] = verb_score
    score += verb_score

    quant_score = min(weights["quantified"], len(quantified) * 3)
    breakdown["Quantified achievements"] = quant_score
    score += quant_score

    word_count = len(text.split())
    if 300 <= word_count <= 1200:
        length_score = weights["length"]
    elif word_count < 300:
        length_score = weights["length"] // 2
    else:
        length_score = round(weights["length"] * 0.7)
    breakdown["Length appropriateness"] = length_score
    score += length_score

    contact = extract_contact_info(text)
    if weights["contact"]:
        if contact["email"] and contact["phone"]:
            contact_score = weights["contact"]
        elif contact["email"] or contact["phone"]:
            contact_score = round(weights["contact"] * 0.6)
        else:
            contact_score = 0
        breakdown["Contact info present"] = contact_score
        score += contact_score

    if jd_keywords:
        text_lower = text.lower()
        matched = [k for k in jd_keywords if k in text_lower]
        match_ratio = len(matched) / max(1, len(jd_keywords))
        jd_score = round(match_ratio * weights["jd_match"])
        breakdown["Job description match"] = jd_score
        score += jd_score

    final_score = round(min(100, score))
    return final_score, breakdown
