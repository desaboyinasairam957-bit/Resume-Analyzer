"""
Central configuration for AI Resume Analyzer.
Keep secrets out of source control - this file reads from environment
variables first and falls back to sensible defaults for local dev.
"""

import os

# --- Paths ---------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
GENERATED_RESUME_DIR = os.path.join(BASE_DIR, "generated_resume")
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

SKILLS_CSV = os.path.join(DATA_DIR, "skills.csv")
KEYWORDS_CSV = os.path.join(DATA_DIR, "keywords.csv")
JOB_ROLES_CSV = os.path.join(DATA_DIR, "job_roles.csv")

LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")
STYLE_CSS_PATH = os.path.join(ASSETS_DIR, "style.css")

# --- spaCy / NLTK ----------------------------------------------------------
SPACY_MODEL = "en_core_web_sm"
NLTK_PACKAGES = ["punkt", "punkt_tab", "stopwords"]

# --- Optional AI providers -------------------------------------------------
# Keys are supplied by the user at runtime in the sidebar and never persisted.
# Environment variables are only used as a convenience default for local dev.
OPENAI_API_KEY_DEFAULT = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY_DEFAULT = os.environ.get("GEMINI_API_KEY", "")

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
)

# --- App settings -----------------------------------------------------------
APP_TITLE = "AI Resume Analyzer"
APP_ICON = "📄"
MAX_JD_COMPARE = 5

# ATS score weights - two profiles, selected automatically based on whether
# a job description was provided. Each set sums to 100.

# Used when NO job description is pasted - general resume quality only.
ATS_WEIGHTS_NO_JD = {
    "sections": 30,
    "skills": 25,
    "action_verbs": 20,
    "quantified": 20,
    "length": 5,
    "contact": 0,
    "jd_match": 0,
}

# Used when a job description IS pasted - the JD match dominates the score,
# so the ATS score reflects fit for that specific job rather than generic quality.
ATS_WEIGHTS_WITH_JD = {
    "sections": 10,
    "skills": 10,
    "action_verbs": 10,
    "quantified": 10,
    "length": 5,
    "contact": 5,
    "jd_match": 50,
}

# Job fit weighting
JOB_FIT_WEIGHTS = {
    "keyword_overlap": 0.4,
    "skill_overlap": 0.4,
    "similarity": 0.2,
}

FIT_THRESHOLDS = {"strong": 75, "moderate": 55}


def ensure_directories():
    for d in [UPLOAD_DIR, OUTPUT_DIR, GENERATED_RESUME_DIR]:
        os.makedirs(d, exist_ok=True)
