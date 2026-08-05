"""
analyzer/keyword_match.py
NLTK-based job description keyword extraction, missing-keyword detection,
and the combined Job Fit Verdict (keyword overlap + skill overlap + semantic
similarity + experience-level alignment).
"""

import re
import csv
from collections import Counter

import streamlit as st
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from config import NLTK_PACKAGES, JOB_ROLES_CSV, JOB_FIT_WEIGHTS, FIT_THRESHOLDS
from analyzer.skill_extractor import find_skills


@st.cache_resource
def load_nltk_stopwords():
    for pkg in NLTK_PACKAGES:
        try:
            nltk.data.find(f"tokenizers/{pkg}" if "punkt" in pkg else f"corpora/{pkg}")
        except LookupError:
            nltk.download(pkg, quiet=True)
    return set(stopwords.words("english"))


@st.cache_data
def load_experience_level_terms(csv_path=JOB_ROLES_CSV):
    terms = {"entry": [], "mid": [], "senior": []}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            terms[row["level"]].append(row["term"])
    return terms


EXTRA_STOPWORDS = {
    "job", "role", "team", "work", "working", "experience", "skills",
    "ability", "years", "year", "including", "using", "strong", "must",
}


def extract_keywords_from_jd(jd_text, stopword_set, top_n=40):
    tokens = word_tokenize(jd_text.lower())
    words = [w for w in tokens if w.isalpha() and len(w) > 2 and w not in stopword_set]
    words = [w for w in words if w not in EXTRA_STOPWORDS]
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_n)]


def find_missing_keywords(text, jd_keywords):
    text_lower = text.lower()
    return [k for k in jd_keywords if k not in text_lower]


def detect_required_experience_level(jd_text, level_terms):
    jd_lower = jd_text.lower()
    for level in ["senior", "mid", "entry"]:
        if any(term in jd_lower for term in level_terms[level]):
            return level
    return None


def estimate_candidate_experience_years(text):
    matches = re.findall(r"(\d{1,2})\s*\+?\s*years?", text.lower())
    years = [int(m) for m in matches if int(m) <= 40]
    return max(years) if years else None


def calculate_job_fit(text, doc, found_skills, jd_text, jd_keywords, jd_doc, nlp, matcher, level_terms):
    """
    Combines three signals into one job-fit verdict:
    1. Keyword/skill overlap with the JD (NLTK keywords + spaCy PhraseMatcher)
    2. Semantic similarity between resume and JD (spaCy vector similarity)
    3. Experience-level alignment (junior/mid/senior heuristic)
    """
    text_lower = text.lower()

    matched_kw = [k for k in jd_keywords if k in text_lower]
    keyword_overlap_pct = round(len(matched_kw) / max(1, len(jd_keywords)) * 100)

    jd_skills = find_skills(jd_doc, nlp, matcher)
    jd_skill_set = {s.lower() for skills in jd_skills.values() for s in skills}
    resume_skill_set = {s.lower() for skills in found_skills.values() for s in skills}
    overlapping_skills = jd_skill_set & resume_skill_set
    missing_skills = jd_skill_set - resume_skill_set
    skill_overlap_pct = round(len(overlapping_skills) / max(1, len(jd_skill_set)) * 100) if jd_skill_set else None

    try:
        similarity = round(doc.similarity(jd_doc) * 100)
    except Exception:
        similarity = None

    required_level = detect_required_experience_level(jd_text, level_terms)
    candidate_years = estimate_candidate_experience_years(text)
    level_note = None
    if required_level and candidate_years is not None:
        expected_ranges = {"entry": (0, 2), "mid": (2, 6), "senior": (6, 40)}
        low, high = expected_ranges[required_level]
        if low <= candidate_years <= high:
            level_note = f"Your ~{candidate_years} yrs experience matches the {required_level}-level requirement."
        elif candidate_years < low:
            level_note = f"Job looks {required_level}-level; your resume shows ~{candidate_years} yrs, which may be under-qualified."
        else:
            level_note = f"Job looks {required_level}-level; your resume shows ~{candidate_years} yrs, which may read as over-qualified."
    elif required_level:
        level_note = f"Job appears to target {required_level}-level candidates - couldn't detect your years of experience from the resume text."

    components, weights = [keyword_overlap_pct], [JOB_FIT_WEIGHTS["keyword_overlap"]]
    if skill_overlap_pct is not None:
        components.append(skill_overlap_pct)
        weights.append(JOB_FIT_WEIGHTS["skill_overlap"])
    if similarity is not None:
        components.append(similarity)
        weights.append(JOB_FIT_WEIGHTS["similarity"])

    total_weight = sum(weights)
    fit_score = round(sum(c * w for c, w in zip(components, weights)) / total_weight)

    if fit_score >= FIT_THRESHOLDS["strong"]:
        verdict = "Strong Match"
    elif fit_score >= FIT_THRESHOLDS["moderate"]:
        verdict = "Moderate Match"
    else:
        verdict = "Weak Match"

    return {
        "fit_score": fit_score,
        "verdict": verdict,
        "keyword_overlap_pct": keyword_overlap_pct,
        "skill_overlap_pct": skill_overlap_pct,
        "overlapping_skills": sorted(overlapping_skills),
        "missing_skills": sorted(missing_skills),
        "similarity": similarity,
        "level_note": level_note,
    }
