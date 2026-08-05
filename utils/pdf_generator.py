"""
utils/pdf_generator.py
Renders the improved-resume draft to a PDF file using fpdf2 (lightweight,
pure-Python - no system dependencies like wkhtmltopdf or LaTeX required).
"""

from fpdf import FPDF


class ImprovedResumePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Improved Resume Draft", ln=True)
        self.ln(2)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 30, 30)
        self.cell(0, 8, title, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        # fpdf2's multi_cell handles wrapping; encode to latin-1-safe text
        safe_text = text.encode("latin-1", "replace").decode("latin-1")
        self.multi_cell(0, 6, safe_text)
        self.ln(1)


def generate_improved_resume_pdf(content, output_path):
    """
    content: dict from analyzer.resume_improver.build_improved_resume_content
    output_path: full file path to write the PDF to
    """
    pdf = ImprovedResumePDF()
    pdf.add_page()

    pdf.body_text(content["intro"])
    pdf.ln(3)

    pdf.section_title("Suggested Keywords To Weave In")
    if content["missing_keywords"]:
        pdf.body_text(", ".join(content["missing_keywords"]))
    else:
        pdf.body_text("No job description provided - general improvements applied below.")
    pdf.ln(3)

    pdf.section_title("Improvement Notes")
    for s in content["suggestions"]:
        pdf.body_text(f"- {s}")
    pdf.ln(3)

    pdf.section_title("Original Resume Content")
    pdf.body_text(content["original_text"])

    pdf.output(output_path)
    return output_path
