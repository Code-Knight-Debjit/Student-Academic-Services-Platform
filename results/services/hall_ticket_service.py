"""
PDF generation services for hall tickets and receipts.

LOCATION: results/services/hall_ticket_service.py
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from django.utils import timezone
import qrcode
from datetime import datetime


def generate_hall_ticket_pdf(makeup_request):
    """
    Generate hall ticket PDF for makeup exam.
    
    Args:
        makeup_request: MakeupExamRequest instance
    
    Returns:
        BytesIO buffer containing PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#374151'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    # Header
    title = Paragraph("MAKEUP EXAMINATION HALL TICKET", title_style)
    elements.append(title)
    
    subtitle = Paragraph(f"Exam Cycle: {makeup_request.exam_cycle}", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.3*inch))
    
    # Student Information
    student_heading = Paragraph("Candidate Information", heading_style)
    elements.append(student_heading)
    
    student_data = [
        ['USN:', makeup_request.student.usn],
        ['Name:', makeup_request.student.name],
        ['Department:', makeup_request.student.department or 'N/A'],
        ['Semester:', str(makeup_request.semester)],
    ]
    
    student_table = Table(student_data, colWidths=[2*inch, 4*inch])
    student_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
    ]))
    
    elements.append(student_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Exam Details
    exam_heading = Paragraph("Examination Details", heading_style)
    elements.append(exam_heading)
    
    exam_data = [
        ['Exam Date:', makeup_request.exam_date.strftime('%d %B %Y') if makeup_request.exam_date else 'TBA'],
        ['Reporting Time:', makeup_request.reporting_time.strftime('%I:%M %p') if makeup_request.reporting_time else 'TBA'],
        ['Exam Center:', makeup_request.exam_center or 'Will be notified'],
        ['Payment ID:', makeup_request.razorpay_payment_id],
    ]
    
    exam_table = Table(exam_data, colWidths=[2*inch, 4*inch])
    exam_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
    ]))
    
    elements.append(exam_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Subjects Table
    subjects_heading = Paragraph("Registered Subjects", heading_style)
    elements.append(subjects_heading)
    
    # Table headers
    subjects_data = [['S.No', 'Course Code', 'Course Title']]
    
    # Add subjects
    for idx, subject in enumerate(makeup_request.subjects.all(), 1):
        subjects_data.append([
            str(idx),
            subject.course_code,
            subject.course_title
        ])
    
    subjects_table = Table(subjects_data, colWidths=[0.5*inch, 1.5*inch, 4*inch])
    subjects_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        
        # Padding
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(subjects_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # QR Code (optional - contains hall ticket verification data)
    try:
        qr = qrcode.QRCode(version=1, box_size=4, border=2)
        qr.add_data(f"HALL_TICKET:{makeup_request.student.usn}:{makeup_request.id}:{makeup_request.exam_cycle}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR to buffer
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Add to PDF
        qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
        elements.append(qr_image)
        elements.append(Spacer(1, 0.2*inch))
    except:
        pass  # QR code is optional
    
    # Instructions
    instructions_heading = Paragraph("Important Instructions", heading_style)
    elements.append(instructions_heading)
    
    instructions = [
        "1. Carry this hall ticket and a valid ID proof to the examination center.",
        "2. Report to the exam center at least 30 minutes before the scheduled time.",
        "3. Mobile phones and electronic devices are strictly prohibited in the exam hall.",
        "4. Candidates must follow all exam center rules and regulations.",
        "5. This hall ticket is valid only for the mentioned exam cycle and subjects.",
    ]
    
    for instruction in instructions:
        inst_para = Paragraph(
            instruction,
            ParagraphStyle('Instruction', parent=styles['Normal'], fontSize=9, leftIndent=10)
        )
        elements.append(inst_para)
        elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Signature section
    sig_data = [
        ['___________________', '___________________'],
        ["Candidate's Signature", "Authorized Signature"]
    ]
    
    sig_table = Table(sig_data, colWidths=[3*inch, 3*inch])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(sig_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Footer
    footer_text = Paragraph(
        f"Generated on: {timezone.now().strftime('%d %B %Y, %I:%M %p')} | Hall Ticket ID: {makeup_request.id}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                      textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER)
    )
    elements.append(footer_text)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


# ============================================================================
# RECEIPT GENERATION
# ============================================================================

def generate_revaluation_receipt(reval_request):
    """
    Generate payment receipt for revaluation.
    
    Args:
        reval_request: RevaluationRequest instance
    
    Returns:
        str: URL to receipt (or file path)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    title = Paragraph("PAYMENT RECEIPT", title_style)
    elements.append(title)
    
    subtitle = Paragraph(
        "Revaluation Fee Payment",
        ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=12, 
                      alignment=TA_CENTER, textColor=colors.HexColor('#6b7280'))
    )
    elements.append(subtitle)
    elements.append(Spacer(1, 0.3*inch))
    
    # Receipt details
    receipt_data = [
        ['Receipt No:', str(reval_request.id).zfill(6)],
        ['Payment ID:', reval_request.razorpay_payment_id],
        ['Date:', reval_request.created_at.strftime('%d %B %Y, %I:%M %p')],
        ['', ''],
        ['Student USN:', reval_request.student.usn],
        ['Student Name:', reval_request.student.name],
        ['', ''],
        ['Course Code:', reval_request.result.course.course_code],
        ['Course Title:', reval_request.result.course.course_title],
        ['', ''],
        ['Amount Paid:', f'₹ {reval_request.amount_paid}'],
        ['Payment Status:', 'SUCCESS'],
    ]
    
    receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
    receipt_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, -2), (-1, -2), 2, colors.HexColor('#1e40af')),
    ]))
    
    elements.append(receipt_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Note
    note = Paragraph(
        "This is a computer-generated receipt and does not require a signature.",
        ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, 
                      textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER,
                      fontName='Helvetica-Oblique')
    )
    elements.append(note)
    
    doc.build(elements)
    
    # Save to file or return URL
    # For now, returning buffer - in production, save to media folder and return URL
    receipt_filename = f"receipt_reval_{reval_request.id}.pdf"
    # Save logic here
    
    return f"/media/receipts/{receipt_filename}"  # Placeholder


def generate_makeup_exam_receipt(makeup_request):
    """
    Generate payment receipt for makeup exam.
    
    Args:
        makeup_request: MakeupExamRequest instance
    
    Returns:
        str: URL to receipt
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Similar to revaluation receipt but with subject list
    # Implementation similar to above
    
    receipt_filename = f"receipt_makeup_{makeup_request.id}.pdf"
    return f"/media/receipts/{receipt_filename}"  # Placeholder
