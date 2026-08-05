# AI Resume Analyzer

A modular Streamlit app that analyzes a PDF resume, scores it for ATS
compatibility, verifies fit against a specific job description, finds missing
keywords, and generates a downloadable improved resume PDF.

## Tech Stack
- Python, Streamlit
- NLP: spaCy (skill matching, verb lemmatization, semantic similarity) + NLTK
  (job description keyword frequency analysis)
- PDFPlumber (primary) / PyPDF2 (fallback) for reading resumes
- fpdf2 for generating the improved-resume PDF
- OpenAI API or Gemini API (optional, for AI-enhanced suggestions)

## Project Structure
```
AI_Resume_Analyzer/
│
├── app.py                     # Main Streamlit application (UI wiring only)
├── requirements.txt
├── README.md
├── config.py                  # Paths, weights, API defaults, app settings
│
├── assets/
│   ├── logo.png                # App logo (generated)
│   └── style.css                # Loaded into the page via st.markdown
│
├── uploads/                    # Uploaded resumes are saved here (audit/history)
├── output/                     # Reserved for any generated text/report output
│
├── parser/
│   ├── pdf_parser.py            # PDFPlumber (primary) + PyPDF2 (fallback) reading
│   ├── text_extractor.py        # Turns parsed pages into one text string
│   └── preprocess.py            # Whitespace cleanup + "enough text?" check
│
├── analyzer/
│   ├── skill_extractor.py       # spaCy PhraseMatcher skills + action verbs
│   ├── ats_score.py              # ATS 0-100 score + breakdown
│   ├── keyword_match.py          # NLTK JD keywords, missing keywords, Job Fit Verdict
│   ├── suggestion_engine.py      # Rule-based suggestions + optional OpenAI/Gemini call
│   └── resume_improver.py        # Assembles improved-resume content for the PDF
│
├── data/
│   ├── skills.csv                # category,skill - drives skill_extractor.py
│   ├── keywords.csv              # common ATS buzzwords (reference list)
│   └── job_roles.csv             # level,term - drives experience-level detection
│
├── utils/
│   ├── helper.py                  # Contact info regex extraction
│   ├── pdf_generator.py           # Renders the improved resume to PDF (fpdf2)
│   └── file_handler.py            # Saves uploads/ and generated_resume/ files
│
└── generated_resume/
    └── improved_resume.pdf        # Output of the "Download Improved Resume" button
```

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run app.py
```

NLTK's `punkt` and `stopwords` data download automatically on first run
(cached after that, via `analyzer/keyword_match.py`).

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Features

- **Upload resume (PDF)** - parsed via `parser/pdf_parser.py`
  (PDFPlumber primary, PyPDF2 fallback)
- **Extract skills** - `analyzer/skill_extractor.py` uses spaCy's
  `PhraseMatcher` against the categorized dictionary in `data/skills.csv`
- **ATS score** - `analyzer/ats_score.py` scores section completeness, skill
  coverage, action verbs, quantified achievements, length, and contact info.
  **When you paste a job description, the score is computed directly against
  it**: `config.ATS_WEIGHTS_WITH_JD` shifts 50% of the score onto the
  JD-match component (vs. 0% in `ATS_WEIGHTS_NO_JD` when no JD is given), so
  the number you see reflects fit for that specific job rather than generic
  resume quality
- **Job Fit Verdict** - `analyzer/keyword_match.py::calculate_job_fit`
  combines:
  - keyword overlap (NLTK, weighted 40%)
  - skill overlap between resume and JD (spaCy PhraseMatcher, weighted 40%)
  - semantic similarity (spaCy document vectors, weighted 20%)
  - experience-level alignment (`data/job_roles.csv` terms vs. years detected
    in the resume)
  - Produces a 0-100 fit score and a Strong / Moderate / Weak Match verdict,
    plus the specific skills the job wants that your resume is missing
- **Compare Against Multiple Jobs** - paste 2-5 job postings and rank them by
  fit score against your resume
- **Missing keyword detection** - `analyzer/keyword_match.py` tokenizes the
  JD with NLTK, strips stopwords, ranks frequent terms, checks which are
  absent from the resume
- **Resume improvement suggestions** - rule-based
  (`analyzer/suggestion_engine.py`), optionally enhanced by OpenAI/Gemini if
  you supply an API key in the sidebar (never stored)
- **Download improved resume** - `utils/pdf_generator.py` renders a clean PDF
  via fpdf2, saved to `generated_resume/improved_resume.pdf`

## Configuration (`config.py`)
All paths, ATS scoring weights, job-fit weights, and match thresholds live in
`config.py` so you can tune scoring behavior without touching the analysis
code. API keys default to the `OPENAI_API_KEY` / `GEMINI_API_KEY` environment
variables for local dev convenience, but the sidebar input always takes
precedence and nothing is ever written to disk.

## Extending the data files
- `data/skills.csv` - add a row (`category,skill`) to recognize a new skill;
  no code changes needed
- `data/job_roles.csv` - add a row (`level,term`) to recognize new
  entry/mid/senior phrasing in job postings
- `data/keywords.csv` - reference list of common ATS buzzwords (not yet wired
  into scoring - a natural next step is folding it into `ats_score.py`)

## Other ideas to extend this further
- **Resume version history** - `uploads/` already keeps timestamped copies;
  add a SQLite table to track ATS/fit score over time as you edit
- **Cover letter generator** - reuse `keyword_match.py`'s JD keyword
  extraction to draft a tailored cover letter (needs the optional AI key)
- **Bulk/recruiter mode** - loop `pdf_parser.py` over multiple resumes against
  one job description for a "rank these candidates" view
- **Industry-specific scoring profiles** - add a profile selector that swaps
  which weights in `config.py` (`ATS_WEIGHTS`, `JOB_FIT_WEIGHTS`) apply
- **Readability check** - use spaCy sentence segmentation to flag
  overly long or jargon-heavy bullet points
- **Wire `data/keywords.csv` into ATS scoring** - reward resumes that use the
  common buzzwords, or flag overuse of generic ones
