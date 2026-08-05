"""
analyzer/skill_extractor.py
spaCy-based skill extraction (PhraseMatcher) and action-verb detection
(POS tagging + lemmatization), driven by data/skills.csv.
"""

import csv
import streamlit as st
import spacy
from spacy.matcher import PhraseMatcher

from config import SPACY_MODEL, SKILLS_CSV

ACTION_VERBS = [
    "lead", "build", "develop", "design", "implement", "launch", "create",
    "manage", "optimize", "improve", "increase", "decrease", "reduce",
    "achieve", "deliver", "spearhead", "architect", "streamline",
    "collaborate", "mentor", "coordinate", "analyze", "automate",
    "resolve", "negotiate", "present", "train", "supervise", "execute",
]


@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load(SPACY_MODEL)
    except OSError:
        st.error(
            f"spaCy model '{SPACY_MODEL}' is not installed. Run:\n\n"
            f"    python -m spacy download {SPACY_MODEL}"
        )
        st.stop()


@st.cache_data
def load_skill_database(csv_path=SKILLS_CSV):
    """Loads category -> [skills] from data/skills.csv."""
    db = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.setdefault(row["category"], []).append(row["skill"])
    return db


@st.cache_resource
def build_skill_matcher(_nlp):
    skill_db = load_skill_database()
    matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
    for category, terms in skill_db.items():
        patterns = [_nlp.make_doc(t) for t in terms]
        matcher.add(category, patterns)
    return matcher


def find_skills(doc, nlp, matcher):
    """Returns {category: [skills found]} using the PhraseMatcher."""
    matches = matcher(doc)
    found = {}
    for match_id, start, end in matches:
        category = nlp.vocab.strings[match_id]
        span_text = doc[start:end].text
        found.setdefault(category, set()).add(span_text)
    return {k: sorted(v) for k, v in found.items()}


def find_action_verbs(doc):
    """Uses spaCy lemmatization so tenses all match (led/leading/leads -> lead)."""
    found = [
        token.lemma_.lower()
        for token in doc
        if token.pos_ == "VERB" and token.lemma_.lower() in ACTION_VERBS
    ]
    return sorted(set(found))
