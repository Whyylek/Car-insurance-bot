from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER

def generate_pdf(text: str, filename: str):
    """Generates a PDF document with the given text and saves it under the specified filename."""

    # Create a new PDF document with custom margins
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)

    # Load default styles
    styles = getSampleStyleSheet()

    # Define custom normal text style
    style_normal = ParagraphStyle(
        name='Normal',
        parent=styles['Normal'],
        fontSize=11,
        leading=15
    )

    # Define custom heading style 
    style_heading = ParagraphStyle(
        name='Heading1',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=20
    )

    # List to hold all elements of the PDF
    elements = []

    # Add centered title
    elements.append(Paragraph("Car Insurance Policy Document", style_heading))
    elements.append(Spacer(1, 12))  # Add vertical space

    # Split input text into paragraphs and add them to the document
    paragraphs = [Paragraph(line, style_normal) for line in text.split('\n') if line.strip()]
    for p in paragraphs:
        elements.append(p)
        elements.append(Spacer(1, 10))  # Add small space after each paragraph

    # Build the PDF with all elements
    doc.build(elements)