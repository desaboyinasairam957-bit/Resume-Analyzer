"""
app.py
Main Streamlit application. All heavy logic lives in parser/, analyzer/,
and utils/ - this file wires the UI together.
"""

import streamlit as st

from config import (
    APP_TITLE, APP_ICON, LOGO_PATH, STYLE_CSS_PATH,
    OPENAI_API_KEY_DEFAULT, GEMINI_API_KEY_DEFAULT, MAX_JD_COMPARE,
    ensure_directories,
)

from parser.text_extractor import extract_text
from parser.preprocess import clean_text, is_text_sufficient

from analyzer.skill_extractor import load_spacy_model, build_skill_matcher, find_skills, find_action_verbs
from analyzer.ats_score import check_sections, check_quantified_achievements, calculate_ats_score
from analyzer.keyword_match import (
    load_nltk_stopwords, load_experience_level_terms,
    extract_keywords_from_jd, find_missing_keywords, calculate_job_fit,
)
from analyzer.suggestion_engine import generate_suggestions, get_llm_suggestions
from analyzer.resume_improver import build_improved_resume_content

from utils.helper import extract_contact_info
from utils.file_handler import save_uploaded_resume, generated_resume_path
from utils.pdf_generator import generate_improved_resume_pdf

ensure_directories()

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

# --- Load CSS ---------------------------------------------------------------
try:
    with open(STYLE_CSS_PATH) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# --- Cached resources --------------------------------------------------------
nlp = load_spacy_model()
skill_matcher = build_skill_matcher(nlp)
stopword_set = load_nltk_stopwords()
level_terms = load_experience_level_terms()

# --- Header ------------------------------------------------------------------
header_col1, header_col2 = st.columns([1, 6])
with header_col1:
    try:
        st.image(LOGO_PATH, width=70)
    except Exception:
        pass
with header_col2:
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.caption("Upload your resume (PDF), get an ATS score, a job-fit verdict, and an improved resume draft.")

# --- Sidebar -------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    use_ai = st.checkbox("Enable AI-powered suggestions (optional)", value=False)
    provider, api_key = None, None
    if use_ai:
        provider = st.selectbox("Provider", ["OpenAI", "Gemini"])
        default_key = OPENAI_API_KEY_DEFAULT if provider == "OpenAI" else GEMINI_API_KEY_DEFAULT
        api_key = st.text_input(f"{provider} API Key", type="password", value=default_key)
        st.caption("Your key is used only for this session and never stored.")
    st.divider()
    st.markdown("**Tech used:** Streamlit · spaCy · NLTK · PDFPlumber/PyPDF2 · fpdf2")

# --- Mode & inputs -------------------------------------------------------
mode = st.radio("Mode", ["Single Job Analysis", "Compare Against Multiple Jobs"], horizontal=True)

col1, col2 = st.columns([1, 1])
with col1:
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
with col2:
    if mode == "Single Job Analysis":
        job_description = st.text_area(
            "Paste job description (optional, improves scoring accuracy)",
            height=180,
            placeholder="Paste the job posting here for keyword matching...",
        )
    else:
        st.caption(f"Paste up to {MAX_JD_COMPARE} job postings below to see which one fits your resume best.")
        job_description = ""

analyze_clicked = st.button("🔍 Analyze Resume", type="primary", disabled=uploaded_file is None)

jd_inputs = []
if mode == "Compare Against Multiple Jobs":
    num_jobs = st.number_input("Number of jobs to compare", min_value=2, max_value=MAX_JD_COMPARE, value=2)
    jd_cols = st.columns(min(num_jobs, 3))
    for i in range(num_jobs):
        with jd_cols[i % len(jd_cols)]:
            label = st.text_input(f"Job {i+1} title (optional label)", key=f"jd_label_{i}")
            jd_text = st.text_area(f"Job {i+1} description", height=150, key=f"jd_text_{i}")
            jd_inputs.append((label or f"Job {i+1}", jd_text))

# ---------------------------------------------------------------------------
# Single Job Analysis
# ---------------------------------------------------------------------------

if analyze_clicked and uploaded_file is not None and mode == "Single Job Analysis":
    with st.spinner("Extracting and analyzing your resume..."):
        save_uploaded_resume(uploaded_file)  # persisted to uploads/ for history/audit

        raw_text = extract_text(uploaded_file)
        text = clean_text(raw_text)

        if not is_text_sufficient(text):
            st.error("Couldn't extract meaningful text from this PDF. Try a different export (avoid scanned/image PDFs).")
            st.stop()

        doc = nlp(text)
        found_skills = find_skills(doc, nlp, skill_matcher)
        action_verbs = find_action_verbs(doc)
        sections = check_sections(text)
        quantified = check_quantified_achievements(raw_text)
        contact = extract_contact_info(text)

        jd_keywords = extract_keywords_from_jd(job_description, stopword_set) if job_description.strip() else None
        missing_keywords = find_missing_keywords(text, jd_keywords) if jd_keywords else []

        job_fit = None
        if job_description.strip():
            jd_doc = nlp(job_description)
            job_fit = calculate_job_fit(
                text, doc, found_skills, job_description, jd_keywords, jd_doc,
                nlp, skill_matcher, level_terms,
            )

        ats_score, breakdown = calculate_ats_score(text, found_skills, sections, action_verbs, quantified, jd_keywords)
        suggestions = generate_suggestions(sections, action_verbs, quantified, found_skills, contact, missing_keywords)

        ai_text = None
        if use_ai and api_key:
            with st.spinner(f"Getting suggestions from {provider}..."):
                ai_text = get_llm_suggestions(raw_text, job_description, provider, api_key)

    st.session_state["analysis"] = {
        "raw_text": raw_text, "ats_score": ats_score, "breakdown": breakdown,
        "found_skills": found_skills, "sections": sections, "action_verbs": action_verbs,
        "quantified": quantified, "contact": contact, "missing_keywords": missing_keywords,
        "suggestions": suggestions, "ai_text": ai_text, "job_fit": job_fit,
    }
    st.session_state.pop("multi_fit", None)

# ---------------------------------------------------------------------------
# Compare Against Multiple Jobs
# ---------------------------------------------------------------------------

if analyze_clicked and uploaded_file is not None and mode == "Compare Against Multiple Jobs":
    with st.spinner("Analyzing your resume against each job..."):
        save_uploaded_resume(uploaded_file)

        raw_text = extract_text(uploaded_file)
        text = clean_text(raw_text)

        if not is_text_sufficient(text):
            st.error("Couldn't extract meaningful text from this PDF. Try a different export (avoid scanned/image PDFs).")
            st.stop()

        doc = nlp(text)
        found_skills = find_skills(doc, nlp, skill_matcher)

        results = []
        for label, jd_text in jd_inputs:
            if not jd_text.strip():
                continue
            jd_keywords = extract_keywords_from_jd(jd_text, stopword_set)
            jd_doc = nlp(jd_text)
            fit = calculate_job_fit(
                text, doc, found_skills, jd_text, jd_keywords, jd_doc,
                nlp, skill_matcher, level_terms,
            )
            results.append((label, fit))

        results.sort(key=lambda r: r[1]["fit_score"], reverse=True)

    st.session_state["multi_fit"] = {"results": results, "raw_text": raw_text}
    st.session_state.pop("analysis", None)

# ---------------------------------------------------------------------------
# Render: Compare mode results
# ---------------------------------------------------------------------------

if "multi_fit" in st.session_state and mode == "Compare Against Multiple Jobs":
    mf = st.session_state["multi_fit"]
    st.divider()
    st.subheader("📊 Job Comparison Results")
    if not mf["results"]:
        st.info("Add at least one job description to compare.")
    else:
        best_label, best_fit = mf["results"][0]
        st.success(f"🏆 Best match: **{best_label}** ({best_fit['fit_score']}/100 - {best_fit['verdict']})")
        for label, fit in mf["results"]:
            with st.expander(f"{label} - {fit['fit_score']}/100 ({fit['verdict']})"):
                st.markdown(f"**Keyword overlap:** {fit['keyword_overlap_pct']}%")
                if fit["skill_overlap_pct"] is not None:
                    st.markdown(f"**Skill overlap:** {fit['skill_overlap_pct']}%")
                if fit["similarity"] is not None:
                    st.markdown(f"**Semantic similarity:** {fit['similarity']}%")
                if fit["level_note"]:
                    st.markdown(f"**Experience level:** {fit['level_note']}")
                if fit["missing_skills"]:
                    st.markdown(f"**Missing skills:** {', '.join(fit['missing_skills'])}")

# ---------------------------------------------------------------------------
# Render: Single analysis results
# ---------------------------------------------------------------------------

if "analysis" in st.session_state and mode == "Single Job Analysis":
    a = st.session_state["analysis"]
    has_jd = a.get("job_fit") is not None

    # --- Job Fit Verdict renders FIRST when a JD was supplied - this is the
    # direct, job-description-driven analysis the resume is being judged against.
    if has_jd:
        st.divider()
        jf = a["job_fit"]
        st.subheader("🧭 Job Fit Verdict")
        st.caption("This analysis is computed directly against the job description you pasted.")
        fit_col, detail_col = st.columns([1, 2])
        with fit_col:
            st.metric("Overall Fit", f"{jf['fit_score']} / 100")
            if jf["verdict"] == "Strong Match":
                st.success(f"✅ {jf['verdict']} - your resume looks suitable for this job.")
            elif jf["verdict"] == "Moderate Match":
                st.warning(f"⚠️ {jf['verdict']} - suitable with some gaps to close.")
            else:
                st.error(f"❌ {jf['verdict']} - significant gaps versus this job description.")
        with detail_col:
            st.markdown(f"**Keyword overlap:** {jf['keyword_overlap_pct']}%")
            if jf["skill_overlap_pct"] is not None:
                st.markdown(f"**Skill overlap:** {jf['skill_overlap_pct']}%")
            if jf["similarity"] is not None:
                st.markdown(f"**Semantic similarity:** {jf['similarity']}%")
            if jf["level_note"]:
                st.markdown(f"**Experience level:** {jf['level_note']}")
        if jf["overlapping_skills"]:
            st.markdown(f"**Matching skills:** {', '.join(jf['overlapping_skills'])}")
        if jf["missing_skills"]:
            st.markdown(f"**Skills the JD wants but your resume lacks:** {', '.join(jf['missing_skills'])}")

    st.divider()
    score_col, gauge_col = st.columns([1, 2])
    with score_col:
        score_label = "ATS Score (vs. this job)" if has_jd else "ATS Score"
        st.metric(score_label, f"{a['ats_score']} / 100")
        if a["ats_score"] >= 80:
            st.success("Strong ATS compatibility")
        elif a["ats_score"] >= 60:
            st.warning("Moderate - room to improve")
        else:
            st.error("Needs significant improvement")
    with gauge_col:
        st.markdown("**Score Breakdown**" + (" (job-description-weighted)" if has_jd else ""))
        for label, val in a["breakdown"].items():
            st.progress(min(val / 50, 1.0), text=f"{label}: {val} pts")

    st.divider()
    tab1, tab2, tab3, tab4 = st.tabs(["🧠 Skills Found", "📋 Sections", "🎯 Missing Keywords", "✨ Suggestions"])
    with tab1:
        if a["found_skills"]:
            for category, skills in a["found_skills"].items():
                st.markdown(f"**{category}**")
                st.write(", ".join(skills))
        else:
            st.info("No recognized skills found. Consider adding a dedicated Skills section.")
    with tab2:
        for name, present in a["sections"].items():
            st.checkbox(name, value=present, disabled=True)
        st.markdown(f"**Action verbs detected:** {len(a['action_verbs'])} - {', '.join(a['action_verbs'][:15]) or 'none'}")
        st.markdown(f"**Quantified achievement lines:** {len(a['quantified'])}")
    with tab3:
        if a["missing_keywords"]:
            st.write("These keywords from the job description were not found in your resume:")
            st.write(", ".join(a["missing_keywords"]))
        else:
            st.info("Paste a job description above to see missing keyword analysis.")
    with tab4:
        for s in a["suggestions"]:
            st.markdown(f"- {s}")
        if a["ai_text"]:
            st.markdown("### 🤖 AI-Powered Suggestions")
            st.markdown(a["ai_text"])

    st.divider()
    st.subheader("📥 Download Improved Resume Draft")
    content = build_improved_resume_content(a["raw_text"], a["missing_keywords"], a["suggestions"])
    pdf_path = generated_resume_path("improved_resume.pdf")
    generate_improved_resume_pdf(content, pdf_path)
    with open(pdf_path, "rb") as f:
        st.download_button(
            "Download Improved Resume (.pdf)",
            data=f.read(),
            file_name="improved_resume.pdf",
            mime="application/pdf",
        )
