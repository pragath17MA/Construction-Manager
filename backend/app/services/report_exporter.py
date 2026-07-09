import csv
import io
from io import BytesIO
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app.models.worker import WorkerSchedule
from app.models.material import Material

class ReportExporter:
    @staticmethod
    def generate_worker_report_pdf(
        project_name: str,
        schedules: List[WorkerSchedule],
        shortages: List[str],
        summary: str
    ) -> BytesIO:
        """
        Compiles worker shift schedules, skill distribution, shortage warnings,
        and AI recommendations into a styled PDF.
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
        
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=4
        )
        
        section_heading = ParagraphStyle(
            'SecHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        
        warning_style = ParagraphStyle(
            'Warning',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#b91c1c')
        )

        story = []
        
        # Header Box
        header_data = [
            [
                Paragraph("<b>APEXBuild</b><br/><font size=7 color='#64748b'>Labor Operations Cockpit</font>", title_style),
                Paragraph(f"<b>SHIFT SCHEDULING REPORT</b><br/>Project: {project_name}", body_style)
            ]
        ]
        header_table = Table(header_data, colWidths=[3.5*inch, 4.0*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(header_table)
        
        # Divider
        divider = Table([['']], colWidths=[7.5*inch])
        divider.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#cbd5e1')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(divider)

        # AI Optimization recommendations
        if summary:
            story.append(Paragraph("AI Shift Optimization Recommendations", section_heading))
            story.append(Paragraph(summary.replace("\n", "<br/>"), body_style))
            story.append(Spacer(1, 10))

        # Shortages warnings if present
        if shortages:
            warnings_flow = [
                Paragraph("Critical Labor Shortages Predicted", section_heading)
            ]
            for warn in shortages:
                warnings_flow.append(Paragraph(f"• {warn}", warning_style))
            warnings_flow.append(Spacer(1, 10))
            story.append(KeepTogether(warnings_flow))

        # Active Schedule roster Table
        story.append(Paragraph("Active Worker Shift Allocation Roster", section_heading))
        table_data = [[
            Paragraph("<b>Worker Name</b>", body_style),
            Paragraph("<b>Role / Trade</b>", body_style),
            Paragraph("<b>Assigned Shift</b>", body_style),
            Paragraph("<b>Start Date</b>", body_style),
            Paragraph("<b>End Date</b>", body_style)
        ]]
        
        for s in schedules:
            table_data.append([
                Paragraph(s.worker.full_name, body_style),
                Paragraph(s.worker.role_title, body_style),
                Paragraph(s.shift_type, body_style),
                Paragraph(s.start_date.strftime("%Y-%m-%d"), body_style),
                Paragraph(s.end_date.strftime("%Y-%m-%d"), body_style)
            ])
            
        roster_table = Table(table_data, colWidths=[2.0*inch, 1.8*inch, 1.2*inch, 1.25*inch, 1.25*inch])
        roster_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(roster_table)

        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_materials_csv(materials: List[Material]) -> str:
        """Compiles materials estimate list into a CSV text block."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(["Material Name", "Category", "Quantity Needed", "Unit", "Unit Price", "Total Estimated Cost"])
        
        for m in materials:
            writer.writerow([
                m.material_name,
                m.category,
                float(m.quantity),
                m.unit,
                float(m.unit_price),
                float(m.total_cost)
            ])
            
        return output.getvalue()

    @staticmethod
    def generate_attendance_csv(attendance_list: list) -> str:
        """Compiles attendance logs into a CSV text block."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(["Date", "Worker Name", "Role / Title", "Status", "Hours Worked", "Overtime Hours"])
        
        for att in attendance_list:
            writer.writerow([
                att.date.strftime("%Y-%m-%d"),
                att.worker.full_name,
                att.worker.role_title,
                att.status,
                float(att.hours_worked),
                float(att.overtime_hours)
            ])
            
        return output.getvalue()
