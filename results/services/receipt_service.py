"""
Receipt generation service with proper file storage.

LOCATION: results/services/receipt_service.py
"""

import os
from io import BytesIO
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from django.utils import timezone


def save_pdf_to_media(pdf_buffer, folder, filename):
    """
    Save PDF buffer to media directory and return URL.
    
    Args:
        pdf_buffer: BytesIO buffer containing PDF
        folder: Subfolder in media/receipts/ (e.g., 'revaluation')
        filename: Name of PDF file
    
    Returns:
        str: URL path to saved PDF
    """
    # Create directory if it doesn't exist
    directory = os.path.join(settings.MEDIA_ROOT, 'receipts', folder)
    os.makedirs(directory, exist_ok=True)
    
    # Full file path
    file_path = os.path.join(directory, filename)
    
    # Save PDF to file
    with open(file_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    # Return URL path
    url_path = f"{settings.MEDIA_URL}receipts/{folder}/{filename}"
    return url_path


def generate_revaluation_receipt(reval_request):
    """
    Generate and save payment receipt for revaluation.
    
    Args:
        reval_request: RevaluationRequest instance
    
    Returns:
        str: URL to saved receipt PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=30
    )
    
    # Title
    title = Paragraph("PAYMENT RECEIPT", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Revaluation Fee Payment", subtitle_style)
    elements.append(subtitle)
    
    # Receipt Information
    receipt_data = [
        ['Receipt No:', f"REV-{str(reval_request.id).zfill(6)}"],
        ['Payment ID:', reval_request.razorpay_payment_id or 'N/A'],
        ['Order ID:', reval_request.razorpay_order_id],
        ['Date:', reval_request.created_at.strftime('%d %B %Y, %I:%M %p')],
        ['', ''],
        ['Student USN:', reval_request.student.usn],
        ['Student Name:', reval_request.student.name],
        ['', ''],
        ['Course Code:', reval_request.result.course.course_code],
        ['Course Title:', reval_request.result.course.course_title],
        ['Semester:', str(reval_request.result.semester)],
        ['', ''],
        ['Amount Paid:', f'₹ {reval_request.amount_paid}'],
        ['Payment Status:', 'SUCCESS'],
        ['Payment Method:', 'Razorpay'],
    ]
    
    receipt_table = Table(receipt_data, colWidths=[2.5*inch, 4*inch])
    receipt_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, -3), (-1, -3), 2, colors.HexColor('#1e40af')),
        ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#f3f4f6')),
    ]))
    
    elements.append(receipt_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer note
    note = Paragraph(
        "This is a computer-generated receipt and does not require a signature. "
        "Please retain this receipt for your records.",
        ParagraphStyle(
            'Note',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
    )
    elements.append(note)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Institution details (customize as needed)
    footer = Paragraph(
        f"Generated on: {timezone.now().strftime('%d %B %Y, %I:%M %p')}<br/>"
        "Student Results System | Contact: support@yourschool.edu",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9ca3af'),
            alignment=TA_CENTER
        )
    )
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Save to media folder
    filename = f"receipt_reval_{reval_request.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    receipt_url = save_pdf_to_media(buffer, 'revaluation', filename)
    
    return receipt_url


def generate_makeup_exam_receipt(makeup_request):
    """
    Generate and save payment receipt for makeup exam.
    
    Args:
        makeup_request: MakeupExamRequest instance
    
    Returns:
        str: URL to saved receipt PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=30
    )
    
    # Title
    title = Paragraph("PAYMENT RECEIPT", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Makeup Examination Registration Fee", subtitle_style)
    elements.append(subtitle)
    
    # Receipt Information
    receipt_data = [
        ['Receipt No:', f"MAKEUP-{str(makeup_request.id).zfill(6)}"],
        ['Payment ID:', makeup_request.razorpay_payment_id or 'N/A'],
        ['Order ID:', makeup_request.razorpay_order_id],
        ['Date:', makeup_request.created_at.strftime('%d %B %Y, %I:%M %p')],
        ['', ''],
        ['Student USN:', makeup_request.student.usn],
        ['Student Name:', makeup_request.student.name],
        ['Semester:', str(makeup_request.semester)],
        ['Exam Cycle:', makeup_request.exam_cycle],
        ['', ''],
        ['Number of Subjects:', str(makeup_request.get_subject_count())],
        ['', ''],
    ]
    
    receipt_table = Table(receipt_data, colWidths=[2.5*inch, 4*inch])
    receipt_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(receipt_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Subjects table
    subjects_heading = Paragraph(
        "Registered Subjects",
        ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12, 
                      textColor=colors.HexColor('#374151'), spaceAfter=10)
    )
    elements.append(subjects_heading)
    
    subjects_data = [['S.No', 'Course Code', 'Course Title']]
    for idx, subject in enumerate(makeup_request.subjects.all(), 1):
        subjects_data.append([
            str(idx),
            subject.course_code,
            subject.course_title
        ])
    
    subjects_table = Table(subjects_data, colWidths=[0.5*inch, 1.5*inch, 4.5*inch])
    subjects_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(subjects_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Amount section
    amount_data = [
        ['Amount Paid:', f'₹ {makeup_request.amount_paid}'],
        ['Payment Status:', 'SUCCESS'],
        ['Payment Method:', 'Razorpay'],
    ]
    
    amount_table = Table(amount_data, colWidths=[2.5*inch, 4*inch])
    amount_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#1e40af')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3f4f6')),
    ]))
    
    elements.append(amount_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer note
    note = Paragraph(
        "This is a computer-generated receipt and does not require a signature. "
        "Please retain this receipt for your records and verification purposes.",
        ParagraphStyle(
            'Note',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
    )
    elements.append(note)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer = Paragraph(
        f"Generated on: {timezone.now().strftime('%d %B %Y, %I:%M %p')}<br/>"
        "Student Results System | Contact: support@yourschool.edu",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9ca3af'),
            alignment=TA_CENTER
        )
    )
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Save to media folder
    filename = f"receipt_makeup_{makeup_request.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    receipt_url = save_pdf_to_media(buffer, 'makeup_exam', filename)
    
    return receipt_url


def generate_hall_ticket_file(makeup_request):
    """
    Generate and save hall ticket PDF.
    
    Args:
        makeup_request: MakeupExamRequest instance
    
    Returns:
        str: URL to saved hall ticket PDF
    """
    from .hall_ticket_service import generate_hall_ticket_pdf
    
    # Generate PDF
    pdf_buffer = generate_hall_ticket_pdf(makeup_request)
    
    # Save to media folder
    directory = os.path.join(settings.MEDIA_ROOT, 'hall_tickets')
    os.makedirs(directory, exist_ok=True)
    
    filename = f"hall_ticket_{makeup_request.student.usn}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(directory, filename)
    
    with open(file_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    # Return URL
    url_path = f"{settings.MEDIA_URL}hall_tickets/{filename}"
    return url_path