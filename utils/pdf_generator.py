from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER

def generate_pdf(text: str, filename: str):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()

    # Кастомні стилі
    style_normal = ParagraphStyle(
        name='Normal',
        parent=styles['Normal'],
        fontSize=11,
        leading=15
    )

    style_heading = ParagraphStyle(
        name='Heading1',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=20
    )

    elements = []

    # Заголовок
    elements.append(Paragraph("Car Insurance Policy Document", style_heading))
    elements.append(Spacer(1, 12))

    # Додаємо абзаци
    paragraphs = [Paragraph(line, style_normal) for line in text.split('\n') if line.strip()]
    for p in paragraphs:
        elements.append(p)
        elements.append(Spacer(1, 10))

    doc.build(elements)
