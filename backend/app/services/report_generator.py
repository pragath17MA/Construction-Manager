import csv
import io
from io import BytesIO
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class ReportGenerator:
    @staticmethod
    def _create_base_pdf(title_text: str, project_name: str, subtitle_text: str = "") -> tuple:
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
        
        bold_body = ParagraphStyle(
            'BoldBody',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#1e293b')
        )

        story = []
        
        # Header Box
        header_data = [
            [
                Paragraph(f"<b>APEXBuild</b><br/><font size=7 color='#64748b'>{subtitle_text or 'Operational Analytics Engine'}</font>", title_style),
                Paragraph(f"<b>{title_text.upper()}</b><br/>Project: {project_name}", body_style)
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
        
        return doc, story, styles, title_style, section_heading, body_style, bold_body, buffer

    @staticmethod
    def generate_risk_report_pdf(project_name: str, risk_data: Dict[str, Any]) -> BytesIO:
        """Compiles risk scores, category severities and mitigation strategies into a PDF."""
        doc, story, styles, _, section_heading, body_style, bold_body, buffer = ReportGenerator._create_base_pdf(
            "Risk Assessment & Predictions", project_name, "Security & Hazards Ledger"
        )
        
        risk = risk_data.get("risk")
        delay = risk_data.get("delay_prediction")
        weather = risk_data.get("weather")
        
        if not risk:
            story.append(Paragraph("No risk parameters analyzed yet for this project.", body_style))
            doc.build(story)
            buffer.seek(0)
            return buffer

        # Score summaries
        score_data = [
            [
                Paragraph("<b>Composite Risk Index:</b>", body_style),
                Paragraph(f"<font color='#ef4444'><b>{risk.risk_score} / 100</b></font>", bold_body),
                Paragraph("<b>Delay Probability:</b>", body_style),
                Paragraph(f"<b>{float(risk.delay_probability)}%</b>", bold_body)
            ]
        ]
        score_table = Table(score_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 2.1*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 10))

        # Weather card if present
        if weather:
            story.append(Paragraph("Live Weather Alerts Context", section_heading))
            weather_text = (
                f"Location: {weather.location} | Temp: {float(weather.temperature or 0)}°C | Wind: {float(weather.wind_speed or 0)} km/h<br/>"
                f"Forecast: {weather.weather_description or 'Clear'} | Alerts: <b>{weather.alerts or 'No alerts active'}</b>"
            )
            story.append(Paragraph(weather_text, body_style))
            story.append(Spacer(1, 10))

        # Categories list table
        story.append(Paragraph("Risk Category Breakdown Ratings", section_heading))
        cat_data = [
            [Paragraph("<b>Category</b>", body_style), Paragraph("<b>Calculated Severity</b>", body_style)],
            [Paragraph("Weather Delay Risks", body_style), Paragraph(risk.weather_risk_severity, bold_body)],
            [Paragraph("Material Shortage Risks", body_style), Paragraph(risk.material_risk_severity, bold_body)],
            [Paragraph("Budget Overruns Risks", body_style), Paragraph(risk.budget_risk_severity, bold_body)],
            [Paragraph("Labor Workforce Shortages", body_style), Paragraph(risk.worker_risk_severity, bold_body)],
            [Paragraph("Equipment Failure Downtime", body_style), Paragraph(risk.equipment_risk_severity, bold_body)],
            [Paragraph("Supplier Logistics Bottlenecks", body_style), Paragraph(risk.supplier_risk_severity, bold_body)],
            [Paragraph("Safety Incidents & Hazards", body_style), Paragraph(risk.safety_risk_severity, bold_body)],
            [Paragraph("Timeline & Sequence Delays", body_style), Paragraph(risk.timeline_risk_severity, bold_body)]
        ]
        cat_table = Table(cat_data, colWidths=[3.5*inch, 4.0*inch])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 12))

        # Executive summary and suggestions
        story.append(Paragraph("Executive Risk Narrative Summary", section_heading))
        story.append(Paragraph(risk.executive_summary or "No summary drafted.", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("AI-Recommended Recovery Mitigation Plan", section_heading))
        suggestions_text = risk.ai_mitigation_suggestions or "Review schedules regularly."
        story.append(Paragraph(suggestions_text.replace("\n", "<br/>"), body_style))

        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_progress_report_pdf(project_name: str, progress_data: Dict[str, Any]) -> BytesIO:
        """Compiles completion, milestones tracking and daily updates into a PDF."""
        doc, story, styles, _, section_heading, body_style, bold_body, buffer = ReportGenerator._create_base_pdf(
            "Project Progress & Roster Summary", project_name, "Construction Analytics Cockpit"
        )
        
        milestones = progress_data.get("milestones", [])
        latest_logs = progress_data.get("latest_logs", [])
        
        # Summary details cards
        summary_data = [
            [
                Paragraph("<b>Overall Completion %:</b>", body_style),
                Paragraph(f"<b>{float(progress_data.get('overall_completion', 0))}%</b>", bold_body),
                Paragraph("<b>Timeline Variance:</b>", body_style),
                Paragraph(f"<b>{progress_data.get('planned_vs_actual_variance', 0)} Days Delay</b>", bold_body)
            ],
            [
                Paragraph("<b>Budget Expended:</b>", body_style),
                Paragraph(f"<b>₹{float(progress_data.get('budget_spent', 0)):,.2f}</b>", bold_body),
                Paragraph("<b>Utilization Ratio:</b>", body_style),
                Paragraph(f"<b>{float(progress_data.get('resource_utilization', 85))}%</b>", bold_body)
            ]
        ]
        summary_table = Table(summary_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 2.1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f1f5f9')),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 10))

        # Milestones lists
        story.append(Paragraph("Project Milestone Scheduling Logs", section_heading))
        ms_data = [[
            Paragraph("<b>Milestone Item</b>", body_style),
            Paragraph("<b>Target End Date</b>", body_style),
            Paragraph("<b>Completion %</b>", body_style),
            Paragraph("<b>Status</b>", body_style)
        ]]
        
        for m in milestones:
            ms_data.append([
                Paragraph(m.milestone_name, body_style),
                Paragraph(m.planned_end_date.strftime("%Y-%m-%d"), body_style),
                Paragraph(f"{float(m.completion_percentage)}%", body_style),
                Paragraph(m.status, bold_body)
            ])
            
        ms_table = Table(ms_data, colWidths=[2.8*inch, 1.6*inch, 1.4*inch, 1.7*inch])
        ms_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(ms_table)
        story.append(Spacer(1, 12))

        # Recent daily site logs
        story.append(Paragraph("Recent Daily Update Logs (Site Engineers)", section_heading))
        if not latest_logs:
            story.append(Paragraph("No daily logs recorded yet for this project phase.", body_style))
        else:
            for log in latest_logs:
                log_box = [
                    Paragraph(f"<b>Date: {log.log_date.strftime('%Y-%m-%d')}</b>", bold_body),
                    Paragraph(log.update_text, body_style)
                ]
                if log.image_path:
                    log_box.append(Paragraph(f"<font size=7 color='#64748b'>Linked Image: {log.image_path}</font>", body_style))
                story.append(KeepTogether(log_box))
                story.append(Spacer(1, 6))

        # Modules 10 & 11 Integrations: Visual Audits & Voice commands
        visual_analyses = progress_data.get("visual_analyses", [])
        if visual_analyses:
            story.append(Spacer(1, 10))
            story.append(Paragraph("AI Site Image Visual Safety Audits", section_heading))
            for va in visual_analyses:
                issues = []
                if va.safety_issues:
                    try:
                        issues = json.loads(va.safety_issues)
                    except Exception:
                        issues = [va.safety_issues]
                
                issues_str = ", ".join(issues) if issues else "No hazards detected."
                audit_flow = [
                    Paragraph(f"<b>Image ID: {va.site_image_id}</b> | Stage: {va.construction_stage} | Completion: {float(va.progress_percentage)}%", bold_body),
                    Paragraph(f"<b>Detected Hazards:</b> {issues_str}", body_style)
                ]
                if va.recommendations:
                    audit_flow.append(Paragraph(f"<b>AI Recommendations:</b> {va.recommendations}", body_style))
                story.append(KeepTogether(audit_flow))
                story.append(Spacer(1, 6))

        voice_logs = progress_data.get("voice_logs", [])
        if voice_logs:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Recent AI Voice Command Logs", section_heading))
            voice_data = [[
                Paragraph("<b>Date / Time</b>", body_style),
                Paragraph("<b>Voice Query</b>", body_style),
                Paragraph("<b>System Narrative Response</b>", body_style)
            ]]
            for vl in voice_logs[:5]: # show recent 5
                voice_data.append([
                    Paragraph(vl.created_at.strftime("%Y-%m-%d %H:%M"), body_style),
                    Paragraph(vl.command_text, body_style),
                    Paragraph(vl.response_text, body_style)
                ])
            voice_table = Table(voice_data, colWidths=[1.5*inch, 2.0*inch, 4.0*inch])
            voice_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0,0), (-1,-1), 4),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(voice_table)

        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_risk_excel_csv(history_list: List[Any]) -> str:
        """Generates raw risk history spreadsheet."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Log Date", "Risk Score Index", "Delay Probability", "Executive Risk Summary"])
        for h in history_list:
            writer.writerow([
                h.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                h.risk_score,
                float(h.delay_probability),
                h.executive_summary or ""
            ])
        return output.getvalue()

    @staticmethod
    def generate_progress_excel_csv(milestones: List[Any], reports: List[Any]) -> str:
        """Generates raw milestone and progress reports spreadsheet."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["MILESTONES TRACKING LEDGER"])
        writer.writerow(["Milestone Name", "Target End Date", "Actual End Date", "Completion %", "Roster Status", "Description"])
        for m in milestones:
            writer.writerow([
                m.milestone_name,
                m.planned_end_date.strftime("%Y-%m-%d"),
                m.actual_end_date.strftime("%Y-%m-%d") if m.actual_end_date else "Not Completed",
                float(m.completion_percentage),
                m.status,
                m.description or ""
            ])
            
        writer.writerow([])
        writer.writerow([])
        writer.writerow(["PROGRESS REPORTS LOGS"])
        writer.writerow(["Snapshot Date", "Report Type", "Overall Completion %", "Variance Status", "Milestones Completed Count", "Budget Spent So Far"])
        for r in reports:
            writer.writerow([
                r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                r.report_type,
                float(r.overall_completion_percentage),
                r.variance_status,
                r.milestones_completed_count,
                float(r.budget_spent_so_far)
            ])
            
        return output.getvalue()

    @staticmethod
    def generate_invoice_report_pdf(project_name: str, invoice: Any, analysis_data: Dict[str, Any]) -> BytesIO:
        """Compiles invoice OCR data, budget variance audits, and fraud risk scores into a PDF."""
        doc, story, styles, _, section_heading, body_style, bold_body, buffer = ReportGenerator._create_base_pdf(
            "Invoice Audit & Reconciliation", project_name, "Financial Compliance Ledger"
        )
        
        # Overview Cards
        summary_data = [
            [
                Paragraph("<b>Invoice Number:</b>", body_style),
                Paragraph(invoice.invoice_number or "N/A", bold_body),
                Paragraph("<b>Invoice Date:</b>", body_style),
                Paragraph(invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else "N/A", bold_body)
            ],
            [
                Paragraph("<b>Vendor Name:</b>", body_style),
                Paragraph(invoice.vendor_name or "N/A", bold_body),
                Paragraph("<b>Vendor GST:</b>", body_style),
                Paragraph(invoice.vendor_gst or "N/A", bold_body)
            ],
            [
                Paragraph("<b>Total Amount:</b>", body_style),
                Paragraph(f"<b>₹{float(invoice.total_amount):,.2f}</b>", bold_body),
                Paragraph("<b>OCR Confidence:</b>", body_style),
                Paragraph(f"<b>{float(invoice.confidence_score)}%</b>", bold_body)
            ],
            [
                Paragraph("<b>Audit Status:</b>", body_style),
                Paragraph(f"<font color='#f59e0b'><b>{invoice.status}</b></font>", bold_body),
                Paragraph("<b>Fraud Risk Score:</b>", body_style),
                Paragraph(f"<b>{float(analysis_data.get('fraud_risk_score', 0))}/100</b>", bold_body)
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 2.1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 5),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f1f5f9')),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 10))

        # Invoice Items List
        story.append(Paragraph("Extracted Invoice Line Items", section_heading))
        item_data = [[
            Paragraph("<b>Item Description</b>", body_style),
            Paragraph("<b>Quantity</b>", body_style),
            Paragraph("<b>Unit Price</b>", body_style),
            Paragraph("<b>Total Price</b>", body_style)
        ]]
        
        for item in invoice.items:
            item_data.append([
                Paragraph(item.description, body_style),
                Paragraph(f"{float(item.quantity)}", body_style),
                Paragraph(f"₹{float(item.unit_price):,.2f}", body_style),
                Paragraph(f"₹{float(item.total_price):,.2f}", bold_body)
            ])
            
        item_table = Table(item_data, colWidths=[3.2*inch, 1.2*inch, 1.5*inch, 1.6*inch])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 12))

        # Budget Comparisons List
        story.append(Paragraph("Budget Allocation Variance Checks", section_heading))
        if not invoice.comparisons:
            story.append(Paragraph("No budget items matched for automatic reconciliation.", body_style))
        else:
            comp_data = [[
                Paragraph("<b>Item Name</b>", body_style),
                Paragraph("<b>Budgeted Cost</b>", body_style),
                Paragraph("<b>Actual Cost</b>", body_style),
                Paragraph("<b>Variance</b>", body_style)
            ]]
            for c in invoice.comparisons:
                desc = c.item.description if c.item else "Line Item"
                var_color = '#ef4444' if c.variance > 0 else '#10b981'
                comp_data.append([
                    Paragraph(desc, body_style),
                    Paragraph(f"₹{float(c.budgeted_amount):,.2f}", body_style),
                    Paragraph(f"₹{float(c.actual_amount):,.2f}", body_style),
                    Paragraph(f"<font color='{var_color}'><b>₹{float(c.variance):,.2f}</b></font>", bold_body)
                ])
            comp_table = Table(comp_data, colWidths=[3.2*inch, 1.4*inch, 1.4*inch, 1.5*inch])
            comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(comp_table)
            
        story.append(Spacer(1, 12))

        # Audit Warning & Recommendations
        story.append(Paragraph("AI Compliance & Fraud Findings", section_heading))
        warnings = analysis_data.get("fraud_risk_details", [])
        if not warnings:
            story.append(Paragraph("✓ No anomalies detected.", body_style))
        else:
            for w in warnings:
                story.append(Paragraph(f"<font color='#ef4444'>• {w}</font>", body_style))
                story.append(Spacer(1, 4))
                
        story.append(Spacer(1, 8))
        story.append(Paragraph("AI-Recommended Reconciliation Action Plan", section_heading))
        suggestions = analysis_data.get("ai_fraud_recommendations", "Review invoice quantities.")
        story.append(Paragraph(suggestions.replace("\n", "<br/>"), body_style))

        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_invoice_excel_csv(invoice: Any, comparisons: List[Any]) -> str:
        """Generates raw invoice lines and budget comparisons spreadsheet."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["INVOICE LINE ITEMS"])
        writer.writerow(["Description", "Quantity", "Unit Price", "Total Price"])
        for item in invoice.items:
            writer.writerow([
                item.description,
                float(item.quantity),
                float(item.unit_price),
                float(item.total_price)
            ])
            
        writer.writerow([])
        writer.writerow([])
        writer.writerow(["BUDGET RECONCILIATION VARIANCE"])
        writer.writerow(["Item Description", "Budgeted Cost", "Actual Cost", "Variance Value", "Audit Notes"])
        for c in comparisons:
            desc = c.item.description if c.item else "Line Item"
            writer.writerow([
                desc,
                float(c.budgeted_amount),
                float(c.actual_amount),
                float(c.variance),
                c.analysis_notes or ""
            ])
            
        return output.getvalue()
