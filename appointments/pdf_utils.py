from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
from django.conf import settings
import os

def generate_invoice_pdf(invoice):
    """
    Generate a professional PDF invoice using ReportLab
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Story' elements
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1,  # Center
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
    )
    
    # Company Header
    story.append(Paragraph("Hospital Management System", title_style))
    story.append(Paragraph("Medical Invoice System", ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.HexColor('#34495e'),
        alignment=1,
    )))
    
    # Invoice Info Table
    invoice_data = [
        ['Invoice Number:', invoice.invoice_number],
        ['Invoice Date:', invoice.invoice_date.strftime('%B %d, %Y')],
        ['Due Date:', invoice.due_date.strftime('%B %d, %Y')],
        ['Status:', invoice.get_status_display()],
    ]
    
    if invoice.paid_date:
        invoice_data.append(['Paid Date:', invoice.paid_date.strftime('%B %d, %Y %H:%M')])
    
    invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    story.append(invoice_table)
    story.append(Spacer(1, 20))
    
    # Bill To and Service Details
    billing_data = [
        ['Bill To:', 'Service Details:'],
        [invoice.patient.user.get_full_name(), f"Doctor: Dr. {invoice.doctor.user.get_full_name()}"],
        [invoice.patient.user.email or '', f"Report: {invoice.medical_report.title if invoice.medical_report else 'N/A'}"],
        [invoice.patient.user.phone or '', f"Appointment: {invoice.appointment.patient_name if invoice.appointment else 'N/A'}"],
    ]
    
    billing_table = Table(billing_data, colWidths=[2.5*inch, 3.5*inch])
    billing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(billing_table)
    story.append(Spacer(1, 20))
    
    # Services Table
    services_data = [['Description', 'Amount']]
    services_data.append([invoice.services_description, f"${invoice.consultation_fee:.2f}"])
    
    if invoice.report_fee > 0:
        services_data.append(['Medical Report Processing Fee', f"${invoice.report_fee:.2f}"])
    
    if invoice.additional_charges > 0:
        services_data.append(['Additional Charges', f"${invoice.additional_charges:.2f}"])
    
    if invoice.discount_amount > 0:
        services_data.append(['Discount', f"-${invoice.discount_amount:.2f}"])
    
    if invoice.tax_amount > 0:
        services_data.append(['Tax', f"${invoice.tax_amount:.2f}"])
    
    services_table = Table(services_data, colWidths=[4.5*inch, 1.5*inch])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(services_table)
    story.append(Spacer(1, 20))
    
    # Total Section
    subtotal = invoice.consultation_fee + invoice.report_fee + invoice.additional_charges
    total_data = [
        ['Subtotal:', f"${subtotal:.2f}"],
        ['Discount:', f"-${invoice.discount_amount:.2f}"],
        ['Tax:', f"${invoice.tax_amount:.2f}"],
        ['Total Amount:', f"${invoice.total_amount:.2f}"],
    ]
    
    if invoice.status != 'PAID':
        total_data.append(['Amount Due:', f"${invoice.get_amount_due():.2f}"])
    
    total_table = Table(total_data, colWidths=[4.5*inch, 1.5*inch])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (3, 0), (3, -1), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (3, 0), (3, -1), colors.whitesmoke),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
    ]))
    
    story.append(total_table)
    
    # Notes section
    if invoice.notes:
        story.append(Spacer(1, 20))
        story.append(Paragraph("Notes:", ParagraphStyle(
            'NotesTitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.HexColor('#2c3e50'),
        )))
        story.append(Paragraph(invoice.notes, normal_style))
    
    # Payment information if not paid
    if invoice.status != 'PAID':
        story.append(Spacer(1, 20))
        story.append(Paragraph("Payment Information:", ParagraphStyle(
            'PaymentTitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.HexColor('#2c3e50'),
        )))
        story.append(Paragraph(f"Payment Terms: {invoice.payment_terms}", normal_style))
        story.append(Paragraph("Payment Methods: Cash, Credit Card, Bank Transfer, Online Payment", normal_style))
        story.append(Paragraph(f"For payment inquiries, contact us at: billing@hms.com | Phone: +1 234 567 8900", normal_style))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Thank you for choosing our healthcare services!", ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=1,
        spaceAfter=6,
    )))
    story.append(Paragraph("© 2024 Hospital Management System. All rights reserved.", ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95a5a6'),
        alignment=1,
    )))
    
    # Add watermark if paid
    if invoice.status == 'PAID':
        story.append(Spacer(1, 100))
        story.append(Paragraph("PAID", ParagraphStyle(
            'Watermark',
            parent=styles['Normal'],
            fontSize=60,
            textColor=colors.HexColor('#27ae60'),
            alignment=1,
            rotation=45,
        )))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF value
    pdf_value = buffer.getvalue()
    buffer.close()
    
    return pdf_value

def create_pdf_response(pdf_value, filename):
    """
    Create Django HttpResponse with PDF
    """
    from django.http import HttpResponse
    
    response = HttpResponse(pdf_value, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    response['Content-Length'] = len(pdf_value)
    
    return response
