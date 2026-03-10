import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

out = os.path.join(
    os.path.dirname(__file__),
    "..",
    "outputs",
    "Training_Facility_Drawings_v1.1",
    "PDFs",
    "make_simple_pdf_test.pdf",
)
os.makedirs(os.path.dirname(out), exist_ok=True)
doc = SimpleDocTemplate(out, pagesize=letter)
styles = getSampleStyleSheet()
story = [Paragraph("PDF test", styles["Title"])]
doc.build(story)
print("WROTE:", out)
