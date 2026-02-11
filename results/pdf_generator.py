"""
PDF generation utility for student results.
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_result_pdf(student, metadata, results, semester):
    """
    Generate PDF for student results.
    
    Args:
        student: Student object
        metadata: StudentMetadata object
        results: QuerySet of Result objects
        semester: Semester number
    
    Returns:
        BytesIO buffer containing PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # Title
    title = Paragraph("Student Result Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Student Information
    info_heading = Paragraph("Student Information", heading_style)
    elements.append(info_heading)
    
    info_data = [
        ['USN:', student.usn],
        ['Name:', student.name],
        ['Department:', student.department or 'N/A'],
        ['Date of Birth:', str(metadata.dob)],
        ['Admission Route:', metadata.admission_route or 'N/A'],
        ['Semester:', str(semester)]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Results Table
    results_heading = Paragraph("Academic Results", heading_style)
    elements.append(results_heading)
    
    # Table headers
    table_data = [['S.No', 'Course Code', 'Course Title', 'Marks', 'Marks in Words']]
    
    # Table rows
    for idx, result in enumerate(results, 1):
        table_data.append([
            str(idx),
            result.course.course_code,
            result.course.course_title,
            str(result.final_cie_marks) if result.final_cie_marks else 'N/A',
            result.marks_in_words or 'N/A'
        ])
    
    # Add summary row
    total_marks = sum([r.final_cie_marks for r in results if r.final_cie_marks])
    avg_marks = total_marks / results.count() if results.count() > 0 else 0
    
    table_data.append(['', '', 'Total Marks', str(round(total_marks, 2)), ''])
    table_data.append(['', '', 'Average Marks', str(round(avg_marks, 2)), ''])
    
    # Create table
    results_table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 3*inch, 1*inch, 1.5*inch])
    results_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -3), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -3), 10),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Summary rows
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#f3f4f6')),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -3), [colors.white, colors.HexColor('#f9fafb')]),
        
        # Padding
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(results_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_text = Paragraph(
        f"Generated on: {BytesIO.__name__} • Student Results System",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, 
                      textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER)
    )
    elements.append(footer_text)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer

