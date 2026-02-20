#!/usr/bin/env python3
"""Generate a tailored resume PDF from structured data.

Usage:
    python3 generate_resume_pdf.py --input candidate.json --job-title "Software Engineer" --output resume.pdf

Input JSON schema:
{
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "555-123-4567",
    "summary": "Tailored professional summary...",
    "skills": ["Python", "AWS", ...],
    "experience": [
        {
            "title": "Senior Developer",
            "company": "Acme Corp",
            "dates": "2020-Present",
            "bullets": ["Led team of 5...", "Reduced costs by 30%..."]
        }
    ],
    "education": [
        {
            "degree": "B.S. Computer Science",
            "school": "State University",
            "year": "2018"
        }
    ],
    "certifications": ["AWS Solutions Architect", ...]
}
"""

import json
import argparse
import sys
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.colors import HexColor
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def generate_pdf(data: dict, output_path: str):
    if not HAS_REPORTLAB:
        # Fallback: generate a clean text file
        txt_path = output_path.replace('.pdf', '.txt')
        with open(txt_path, 'w') as f:
            f.write(f"{data['name']}\n")
            f.write(f"{data.get('email', '')} | {data.get('phone', '')}\n")
            f.write("=" * 60 + "\n\n")
            if data.get('summary'):
                f.write(f"{data['summary']}\n\n")
            if data.get('skills'):
                f.write("SKILLS\n")
                f.write(", ".join(data['skills']) + "\n\n")
            if data.get('experience'):
                f.write("EXPERIENCE\n")
                for exp in data['experience']:
                    f.write(f"\n{exp['title']} — {exp['company']} ({exp.get('dates', '')})\n")
                    for b in exp.get('bullets', []):
                        f.write(f"  • {b}\n")
            if data.get('education'):
                f.write("\nEDUCATION\n")
                for edu in data['education']:
                    f.write(f"  {edu['degree']} — {edu['school']} ({edu.get('year', '')})\n")
            if data.get('certifications'):
                f.write("\nCERTIFICATIONS\n")
                for cert in data['certifications']:
                    f.write(f"  • {cert}\n")
        print(f"[WARN] reportlab not installed. Generated text resume: {txt_path}")
        print(f"       Install reportlab for PDF: pip3 install reportlab")
        return txt_path

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            topMargin=0.5*inch, bottomMargin=0.5*inch,
                            leftMargin=0.75*inch, rightMargin=0.75*inch)
    styles = getSampleStyleSheet()
    dark = HexColor("#333333")

    name_style = ParagraphStyle('Name', parent=styles['Title'], fontSize=18,
                                 textColor=dark, spaceAfter=2)
    contact_style = ParagraphStyle('Contact', parent=styles['Normal'], fontSize=10,
                                    textColor=HexColor("#666666"), spaceAfter=6)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12,
                                    textColor=dark, spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
                                 textColor=dark, spaceAfter=2)
    bullet_style = ParagraphStyle('Bullet', parent=body_style, leftIndent=20,
                                   bulletIndent=10, spaceAfter=1)

    story = []
    story.append(Paragraph(data['name'], name_style))
    contact = f"{data.get('email', '')}  |  {data.get('phone', '')}"
    story.append(Paragraph(contact, contact_style))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc")))

    if data.get('summary'):
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
        story.append(Paragraph(data['summary'], body_style))

    if data.get('skills'):
        story.append(Paragraph("SKILLS", section_style))
        story.append(Paragraph(", ".join(data['skills']), body_style))

    if data.get('experience'):
        story.append(Paragraph("EXPERIENCE", section_style))
        for exp in data['experience']:
            title_line = f"<b>{exp['title']}</b> — {exp['company']}  ({exp.get('dates', '')})"
            story.append(Paragraph(title_line, body_style))
            for b in exp.get('bullets', []):
                story.append(Paragraph(f"• {b}", bullet_style))
            story.append(Spacer(1, 4))

    if data.get('education'):
        story.append(Paragraph("EDUCATION", section_style))
        for edu in data['education']:
            line = f"<b>{edu['degree']}</b> — {edu['school']}  ({edu.get('year', '')})"
            story.append(Paragraph(line, body_style))

    if data.get('certifications'):
        story.append(Paragraph("CERTIFICATIONS", section_style))
        for cert in data['certifications']:
            story.append(Paragraph(f"• {cert}", bullet_style))

    doc.build(story)
    print(f"[OK] Generated resume PDF: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate tailored resume PDF")
    parser.add_argument("--input", required=True, help="Path to candidate JSON")
    parser.add_argument("--output", default="resume.pdf", help="Output PDF path")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    generate_pdf(data, args.output)


if __name__ == "__main__":
    main()
