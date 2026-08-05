"""
analyzer/suggestion_engine.py
Rule-based improvement suggestions, plus optional OpenAI/Gemini enhanced
suggestions when the user supplies an API key.
"""

import requests
import streamlit as st

from config import OPENAI_CHAT_URL, OPENAI_MODEL, GEMINI_URL_TEMPLATE, GEMINI_MODEL


def generate_suggestions(sections, action_verbs, quantified, found_skills, contact, missing_keywords):
    suggestions = []
    for name, present in sections.items():
        if not present:
            suggestions.append(f"Add a **{name}** section - ATS systems and recruiters expect it.")
    if not contact["email"]:
        suggestions.append("Add a professional email address near the top of your resume.")
    if len(action_verbs) < 5:
        suggestions.append(
            "Use more **strong action verbs** (led, built, optimized, launched) instead of "
            "passive phrases like 'responsible for'."
        )
    if len(quantified) < 3:
        suggestions.append(
            "**Quantify your impact** - add numbers, percentages, or dollar amounts "
            "(e.g., 'increased efficiency by 30%')."
        )
    if not found_skills:
        suggestions.append("No recognizable skills detected - add a dedicated Skills section.")
    if missing_keywords:
        suggestions.append(f"Your resume is missing these job description keywords: {', '.join(missing_keywords[:10])}")
    if not suggestions:
        suggestions.append("Your resume looks well-structured! Fine-tune wording for the specific role.")
    return suggestions


def _build_prompt(resume_text, job_description):
    return f"""You are an expert resume coach and ATS specialist.
Given the RESUME and the JOB DESCRIPTION below, provide:
1. Three specific rewrite suggestions for weak bullet points (quote original + improved version)
2. Two missing but relevant achievements/skills the candidate should consider adding
3. One sentence overall verdict on ATS readiness

RESUME:
{resume_text[:6000]}

JOB DESCRIPTION:
{job_description[:3000] if job_description else "(none provided - give general improvement advice)"}
"""


def get_llm_suggestions(resume_text, job_description, provider, api_key):
    """Calls OpenAI or Gemini if the user supplies an API key. Returns text or None."""
    if not api_key:
        return None
    prompt = _build_prompt(resume_text, job_description)
    try:
        if provider == "OpenAI":
            resp = requests.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        elif provider == "Gemini":
            url = GEMINI_URL_TEMPLATE.format(model=GEMINI_MODEL, key=api_key)
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        st.warning(f"AI suggestion call failed ({provider}): {e}. Falling back to rule-based analysis only.")
        return None
    return None
