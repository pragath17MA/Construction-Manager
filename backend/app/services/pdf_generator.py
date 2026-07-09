from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from app.models.budget import Budget

def generate_budget_pdf_report(budget: Budget, project_name: str, client_name: str, location: str) -> BytesIO:
    """
    Generates a professionally styled PDF report of a project budget estimate.
    Includes itemized breakdown, metadata, AI summaries, and savings recommendations.
    Uses reportlab flowables to wrap long cell lines securely.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom stylesheet elements matching APEXBuild design language
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#2e3f60'),
        spaceAfter=5
    )
    
    section_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#384f76'),
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#212a3e')
    )
    
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748b')
    )

    story = []
    
    # Header logo/branding box
    header_data = [
        [
            Paragraph("<b>APEXBuild</b><br/><font size=7 color='#64748b'>AI Construction Control Center</font>", title_style),
            Paragraph(f"<b>BUDGET ESTIMATE REPORT</b><br/>Generated: {budget.created_at.strftime('%Y-%m-%d %H:%M')}", meta_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[3.5*inch, 4.0*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    
    # Sleek bottom border line
    divider = Table([['']], colWidths=[7.5*inch])
    divider.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#c8d1e1')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(divider)
    
    # Metadata Overview Cards Panel
    meta_data = [
        [
            Paragraph("<b>Project Name:</b>", body_style), Paragraph(project_name, body_style),
            Paragraph("<b>Currency:</b>", body_style), Paragraph(budget.currency, body_style)
        ],
        [
            Paragraph("<b>Client Name:</b>", body_style), Paragraph(client_name, body_style),
            Paragraph("<b>Estimated Cost:</b>", body_style), Paragraph(f"{float(budget.estimated_cost):,.2f}", body_style)
        ],
        [
            Paragraph("<b>Location:</b>", body_style), Paragraph(location, body_style),
            Paragraph("<b>Optimized Cost:</b>", body_style), Paragraph(f"{float(budget.optimized_cost):,.2f}", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[1.1*inch, 2.65*inch, 1.4*inch, 2.35*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))
    
    # AI Executive Summary Panel
    if budget.ai_summary:
        summary_flow = [
            Paragraph("Executive Summary (AI Generated)", section_heading),
            Paragraph(budget.ai_summary, body_style),
            Spacer(1, 10)
        ]
        story.append(KeepTogether(summary_flow))

    # Itemized Breakdown Table
    story.append(Paragraph("Itemized Budget Breakdown", section_heading))
    table_data = [[
        Paragraph("<b>Category</b>", body_style),
        Paragraph("<b>Description</b>", body_style),
        Paragraph("<b>Qty</b>", body_style),
        Paragraph("<b>Unit Price</b>", body_style),
        Paragraph("<b>Total</b>", body_style)
    ]]
    
    for item in budget.items:
        table_data.append([
            Paragraph(item.category, body_style),
            Paragraph(item.description, body_style),
            Paragraph(f"{float(item.quantity):,.1f}", body_style),
            Paragraph(f"{float(item.unit_price):,.2f}", body_style),
            Paragraph(f"{float(item.total_price):,.2f}", body_style)
        ])
        
    items_table = Table(table_data, colWidths=[1.0*inch, 3.0*inch, 0.7*inch, 1.3*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10))
    
    # AI Optimization recommendations
    if budget.ai_recommendations:
        recs_flow = [
            Paragraph("AI Recommendations & Budget Optimizations", section_heading),
            Paragraph(budget.ai_recommendations.replace("\n", "<br/>"), body_style)
        ]
        story.append(KeepTogether(recs_flow))

    # Compile flow
    doc.build(story)
    buffer.seek(0)
    return buffer
