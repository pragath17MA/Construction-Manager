import os
import csv
import io
from io import BytesIO
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app.models.project import Project, SiteImage, Drawing, Document
from app.models.budget import Budget
from app.models.material import Material, Inventory, Supplier, PurchaseOrder
from app.models.worker import WorkerSchedule, Attendance, Worker
from app.models.risk import Risk, WeatherData, RiskHistory
from app.models.progress import Milestone, ProgressReport as ProgressReportModel
from app.models.invoice import Invoice
from app.models.image_analysis import SiteImageAnalysis
from app.models.chat import ChatSession, ChatMessage
from app.models.voice import VoiceCommandLog
from app.services.pdf_generator import generate_budget_pdf_report
from app.services.report_generator import ReportGenerator
from app.services.report_exporter import ReportExporter

class ReportCenterService:
    @staticmethod
    def _create_styled_pdf(title_text: str, project_name: str, subtitle_text: str = "") -> tuple:
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
            textColor=colors.HexColor('#2e3f60'),
            spaceAfter=4
        )
        
        section_heading = ParagraphStyle(
            'SecHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#384f76'),
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
            textColor=colors.HexColor('#212a3e')
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
                Paragraph(f"<b>APEXBuild</b><br/><font size=7 color='#64748b'>{subtitle_text or 'Management Reporting Ledger'}</font>", title_style),
                Paragraph(f"<b>{title_text.upper()}</b><br/>Project: {project_name}<br/>Generated: {date.today().strftime('%Y-%m-%d')}", body_style)
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
        
        return doc, story, styles, section_heading, body_style, bold_body, buffer

    @staticmethod
    def generate_pdf_report(db: Session, project_id: int, report_type: str) -> BytesIO:
        """Generates any of the 11 PDF report types styled with corporate ReportLab elements."""
        project = db.query(Project).filter(Project.id == project_id).first()
        project_name = project.project_name if project else "Project"
        
        # 1. Budget Report
        if report_type == "budget":
            budget = db.query(Budget).filter(Budget.project_id == project_id).first()
            if not budget:
                raise ValueError("No budget estimates recorded for this project.")
            return generate_budget_pdf_report(budget, project_name, project.client_name, project.location)
            
        # 2. Risk Report
        elif report_type == "risk":
            risk = db.query(Risk).filter(Risk.project_id == project_id).first()
            weather = db.query(WeatherData).filter(WeatherData.project_id == project_id).first()
            risk_data = {"risk": risk, "weather": weather}
            return ReportGenerator.generate_risk_report_pdf(project_name, risk_data)
            
        # 3. Progress Report
        elif report_type == "progress":
            milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
            latest_logs = db.query(ProgressReportModel).filter(ProgressReportModel.project_id == project_id).order_by(ProgressReportModel.created_at.desc()).all()
            progress_data = {
                "overall_completion": sum(m.completion_percentage for m in milestones) / len(milestones) if milestones else 0.0,
                "planned_vs_actual_variance": 0,
                "milestones": milestones,
                "latest_logs": [],
                "reports": latest_logs
            }
            # Add visual analyses & voice logs for Modules 10 and 11 integration
            progress_data["visual_analyses"] = db.query(SiteImageAnalysis).filter(SiteImageAnalysis.project_id == project_id).all()
            progress_data["voice_logs"] = db.query(VoiceCommandLog).filter(VoiceCommandLog.project_id == project_id).limit(5).all()
            return ReportGenerator.generate_progress_report_pdf(project_name, progress_data)
            
        # 4. Worker Report
        elif report_type == "worker":
            schedules = db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
            return ReportExporter.generate_worker_report_pdf(project_name, schedules, [], "Worker roster report compiled.")

        # 5. Material Report
        elif report_type == "material":
            doc, story, styles, sec_heading, body_style, bold_body, buffer = ReportCenterService._create_styled_pdf(
                "Materials Estimation Report", project_name, "Supply Chain Auditing"
            )
            materials = db.query(Material).filter(Material.project_id == project_id).all()
            
            story.append(Paragraph("Estimated Material Consumptions", sec_heading))
            table_data = [[
                Paragraph("<b>Material Item</b>", body_style),
                Paragraph("<b>Category</b>", body_style),
                Paragraph("<b>Qty Needed</b>", body_style),
                Paragraph("<b>Unit Cost</b>", body_style),
                Paragraph("<b>Total Cost</b>", body_style)
            ]]
            for m in materials:
                table_data.append([
                    Paragraph(m.material_name, body_style),
                    Paragraph(m.category, body_style),
                    Paragraph(f"{float(m.quantity):,.2f} {m.unit}", body_style),
                    Paragraph(f"₹{float(m.unit_price):,.2f}", body_style),
                    Paragraph(f"₹{float(m.total_cost):,.2f}", body_style)
                ])
            t = Table(table_data, colWidths=[2.0*inch, 1.5*inch, 1.2*inch, 1.3*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                ('PADDING', (0,0), (-1,-1), 5),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t)
            
            doc.build(story)
            buffer.seek(0)
            return buffer

        # 6. Attendance Report
        elif report_type == "attendance":
            doc, story, styles, sec_heading, body_style, bold_body, buffer = ReportCenterService._create_styled_pdf(
                "Attendance & Labor Hours Ledger", project_name, "Workforce Control Logs"
            )
            # Find worker schedules associated with project
            schedules = db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
            worker_ids = [s.worker_id for s in schedules if s.worker_id]
            
            attendance_list = db.query(Attendance).filter(Attendance.worker_id.in_(worker_ids)).order_by(Attendance.date.desc()).all()
            
            story.append(Paragraph("Attendance Record Log Sheets", sec_heading))
            table_data = [[
                Paragraph("<b>Date</b>", body_style),
                Paragraph("<b>Worker Name</b>", body_style),
                Paragraph("<b>Status</b>", body_style),
                Paragraph("<b>Hours Worked</b>", body_style),
                Paragraph("<b>Overtime Hours</b>", body_style)
            ]]
            for att in attendance_list:
                table_data.append([
                    Paragraph(att.date.strftime("%Y-%m-%d"), body_style),
                    Paragraph(att.worker.full_name if att.worker else "Worker", body_style),
                    Paragraph(att.status, bold_body),
                    Paragraph(f"{float(att.hours_worked):.1f} hrs", body_style),
                    Paragraph(f"{float(att.overtime_hours):.1f} hrs", body_style)
                ])
            t = Table(table_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 1.4*inch, 1.4*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                ('PADDING', (0,0), (-1,-1), 5),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t)
            
            doc.build(story)
            buffer.seek(0)
            return buffer

        # 7. Invoice Report
        elif report_type == "invoice":
            doc, story, styles, sec_heading, body_style, bold_body, buffer = ReportCenterService._create_styled_pdf(
                "Invoice Auditing Ledger", project_name, "Financial Compliance Reviews"
            )
            invoices = db.query(Invoice).filter(Invoice.project_id == project_id).all()
            
            story.append(Paragraph("Received Vendor Invoices", sec_heading))
            table_data = [[
                Paragraph("<b>Invoice ID</b>", body_style),
                Paragraph("<b>Vendor/Path</b>", body_style),
                Paragraph("<b>Amount</b>", body_style),
                Paragraph("<b>Tax</b>", body_style),
                Paragraph("<b>Status</b>", body_style)
            ]]
            for inv in invoices:
                table_data.append([
                    Paragraph(str(inv.id), body_style),
                    Paragraph(os.path.basename(inv.image_path), body_style),
                    Paragraph(f"₹{float(inv.total_amount):,.2f}", body_style),
                    Paragraph(f"₹{float(inv.tax_amount):,.2f}", body_style),
                    Paragraph(inv.status, bold_body)
                ])
            t = Table(table_data, colWidths=[1.0*inch, 2.5*inch, 1.5*inch, 1.3*inch, 1.2*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t)
            
            doc.build(story)
            buffer.seek(0)
            return buffer

        # 8. Image Analysis Report
        elif report_type == "image_analysis":
            doc, story, styles, sec_heading, body_style, bold_body, buffer = ReportCenterService._create_styled_pdf(
                "Visual Threat Detections Report", project_name, "Safety Compliance Ledger"
            )
            analyses = db.query(SiteImageAnalysis).filter(SiteImageAnalysis.project_id == project_id).all()
            
            story.append(Paragraph("Visual Inspection Safety Violations", sec_heading))
            for va in analyses:
                issues = []
                if va.safety_issues:
                    try:
                        issues = json.loads(va.safety_issues)
                    except Exception:
                        issues = [va.safety_issues]
                
                issues_str = ", ".join(issues) if issues else "No hazards."
                item_flow = [
                    Paragraph(f"<b>Image Audit ID: {va.id}</b> | Stage: {va.construction_stage} | Completion: {float(va.progress_percentage)}%", bold_body),
                    Paragraph(f"<b>Detected Hazards:</b> {issues_str}", body_style),
                    Paragraph(f"<b>AI Inspection Recommendations:</b> {va.recommendations or 'None'}", body_style),
                    Spacer(1, 8)
                ]
                story.append(KeepTogether(item_flow))
                
            doc.build(story)
            buffer.seek(0)
            return buffer

        # 9. Drawing Summary Report
        elif report_type == "drawing":
            doc, story, styles, sec_heading, body_style, bold_body, buffer = ReportCenterService._create_styled_pdf(
                "Drawing Specifications Summary", project_name, "AI Blueprint Search Index"
            )
            drawings = db.query(Drawing).filter(Drawing.project_id == project_id).all()
            
            story.append(Paragraph("Uploaded Technical Drawings & Blueprints", sec_heading))
            table_data = [[
                Paragraph("<b>Drawing Name</b>", body_style),
                Paragraph("<b>File Reference</b>", body_style),
                Paragraph("<b>Uploaded Date</b>", body_style)
            ]]
            for d in drawings:
                table_data.append([
                    Paragraph(d.drawing_name, bold_body),
                    Paragraph(os.path.basename(d.drawing_path), body_style),
                    Paragraph(d.uploaded_at.strftime("%Y-%m-%d"), body_style)
                ])
            t = Table(table_data, colWidths=[2.5*inch, 3.5*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t)
            
            doc.build(story)
            buffer.seek(0)
            return buffer

        # 10. Project Summary Report
        elif report_type == "project_summary":
            doc, story, styles, sec_heading, body_style, bold_body, buffer = ReportCenterService._create_styled_pdf(
                "Project Overview Scopes & Roster", project_name, "Apex Executive Ledger"
            )
            story.append(Paragraph("Contract Details Summary", sec_heading))
            meta_data = [
                [Paragraph("<b>Project Scope:</b>", body_style), Paragraph(project.description or "No description", body_style)],
                [Paragraph("<b>Client Name:</b>", body_style), Paragraph(project.client_name, body_style)],
                [Paragraph("<b>Location:</b>", body_style), Paragraph(project.location, body_style)],
                [Paragraph("<b>Budget Limits:</b>", body_style), Paragraph(f"₹{float(project.budget):,.2f}", bold_body)],
                [Paragraph("<b>Contract Timeline:</b>", body_style), Paragraph(f"{project.start_date} to {project.expected_end_date}", body_style)],
                [Paragraph("<b>Current Status:</b>", body_style), Paragraph(project.status, bold_body)]
            ]
            t = Table(meta_data, colWidths=[1.8*inch, 5.7*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
                ('PADDING', (0,0), (-1,-1), 6),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(t)
            
            doc.build(story)
            buffer.seek(0)
            return buffer

        # 11. Executive Dashboard Report
        elif report_type == "executive":
            doc, story, styles, sec_heading, body_style, bold_body, buffer = ReportCenterService._create_styled_pdf(
                "Executive KPI Metrics & Analytics", project_name, "APEXBuild Control Summary"
            )
            # Pull key numbers
            budget = db.query(Budget).filter(Budget.project_id == project_id).first()
            milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
            avg_comp = sum(m.completion_percentage for m in milestones) / len(milestones) if milestones else 0.0
            schedules = db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
            analyses = db.query(SiteImageAnalysis).filter(SiteImageAnalysis.project_id == project_id).all()
            violations = sum(1 for a in analyses if a.safety_issues and len(a.safety_issues) > 2)
            
            story.append(Paragraph("Cross-Module Executive Widgets", sec_heading))
            widgets_data = [
                [
                    Paragraph("<b>Overall Completion %:</b>", body_style), Paragraph(f"{float(avg_comp):.2f}%", bold_body),
                    Paragraph("<b>Budget Expended:</b>", body_style), Paragraph(f"₹{float(budget.total_estimated_cost if budget else 0.0):,.2f}", bold_body)
                ],
                [
                    Paragraph("<b>Active Workers Shift Count:</b>", body_style), Paragraph(str(len(schedules)), body_style),
                    Paragraph("<b>Safety Violations Count:</b>", body_style), Paragraph(str(violations), bold_body)
                ]
            ]
            wt = Table(widgets_data, colWidths=[2.0*inch, 1.7*inch, 2.0*inch, 1.8*inch])
            wt.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(wt)
            
            doc.build(story)
            buffer.seek(0)
            return buffer
            
        else:
            raise ValueError(f"Unknown PDF report type: {report_type}")

    @staticmethod
    def generate_csv_report(db: Session, project_id: int, report_type: str) -> str:
        """Generates tabular spreadsheet report in CSV format."""
        project = db.query(Project).filter(Project.id == project_id).first()
        project_name = project.project_name if project else "Project"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if report_type == "budget":
            budget = db.query(Budget).filter(Budget.project_id == project_id).first()
            writer.writerow(["PROJECT BUDGET ESTIMATION LEDGER"])
            writer.writerow(["Project Name", project_name])
            writer.writerow(["Total Estimated Cost", float(budget.total_estimated_cost) if budget else 0.0])
            writer.writerow(["Total Optimized Cost", float(budget.total_optimized_cost) if budget else 0.0])
            writer.writerow([])
            writer.writerow(["Category", "Description", "Quantity", "Unit Price", "Total Price"])
            if budget and budget.items:
                for item in budget.items:
                    writer.writerow([item.category, item.description, float(item.quantity), float(item.unit_price), float(item.total_price)])
                    
        elif report_type == "material":
            materials = db.query(Material).filter(Material.project_id == project_id).all()
            writer.writerow(["PROJECT MATERIALS ESTIMATED QUANTITIES"])
            writer.writerow(["Material Name", "Category", "Quantity Needed", "Unit", "Unit Price", "Total Cost"])
            for m in materials:
                writer.writerow([m.material_name, m.category, float(m.quantity), m.unit, float(m.unit_price), float(m.total_cost)])
                
        elif report_type == "worker":
            schedules = db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
            writer.writerow(["WORKFORCE ACTIVE SHIFT ROSTER"])
            writer.writerow(["Worker Name", "Role / Title", "Assigned Shift", "Start Date", "End Date"])
            for s in schedules:
                if s.worker:
                    writer.writerow([s.worker.full_name, s.worker.role_title, s.shift_type, s.start_date.strftime("%Y-%m-%d"), s.end_date.strftime("%Y-%m-%d")])
                    
        elif report_type == "attendance":
            schedules = db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
            worker_ids = [s.worker_id for s in schedules if s.worker_id]
            attendance_list = db.query(Attendance).filter(Attendance.worker_id.in_(worker_ids)).order_by(Attendance.date.desc()).all()
            writer.writerow(["WORKFORCE ATTENDANCE HISTORY"])
            writer.writerow(["Date", "Worker Name", "Status", "Hours Worked", "Overtime Hours"])
            for att in attendance_list:
                writer.writerow([att.date.strftime("%Y-%m-%d"), att.worker.full_name if att.worker else "Worker", att.status, float(att.hours_worked), float(att.overtime_hours)])

        elif report_type == "risk":
            history = db.query(RiskHistory).filter(RiskHistory.project_id == project_id).order_by(RiskHistory.created_at.desc()).all()
            writer.writerow(["PROJECT COMPOSITE RISK SCORE HISTORY"])
            writer.writerow(["Date", "Risk Score (0-100)", "Delay Probability %", "Narrative Summary"])
            for h in history:
                writer.writerow([h.created_at.strftime("%Y-%m-%d %H:%M"), h.risk_score, float(h.delay_probability), h.executive_summary or ""])

        elif report_type == "invoice":
            invoices = db.query(Invoice).filter(Invoice.project_id == project_id).all()
            writer.writerow(["RECEIVED INVOICES LEDGER"])
            writer.writerow(["Invoice ID", "File Name", "Total Amount", "Tax Amount", "Status"])
            for inv in invoices:
                writer.writerow([inv.id, os.path.basename(inv.image_path), float(inv.total_amount), float(inv.tax_amount), inv.status])

        elif report_type == "image_analysis":
            analyses = db.query(SiteImageAnalysis).filter(SiteImageAnalysis.project_id == project_id).all()
            writer.writerow(["VISUAL SAFETY AUDIT HAZARDS LOG"])
            writer.writerow(["Audit ID", "Site Image ID", "Construction Stage", "Completion Progress %", "Safety Threats"])
            for va in analyses:
                writer.writerow([va.id, va.site_image_id, va.construction_stage, float(va.progress_percentage), va.safety_issues])

        elif report_type == "drawing":
            drawings = db.query(Drawing).filter(Drawing.project_id == project_id).all()
            writer.writerow(["PROJECT DRAWINGS Blueprints INDEX"])
            writer.writerow(["Drawing Name", "Drawing File Path", "Uploaded At"])
            for d in drawings:
                writer.writerow([d.drawing_name, d.drawing_path, d.uploaded_at.strftime("%Y-%m-%d")])

        elif report_type == "project_summary":
            writer.writerow(["PROJECT SCOPE OVERVIEW"])
            writer.writerow(["Project ID", project.id])
            writer.writerow(["Project Name", project_name])
            writer.writerow(["Location", project.location])
            writer.writerow(["Client", project.client_name])
            writer.writerow(["Start Date", project.start_date.strftime("%Y-%m-%d")])
            writer.writerow(["End Date", project.expected_end_date.strftime("%Y-%m-%d")])
            writer.writerow(["Status", project.status])
            writer.writerow(["Budget Limit", float(project.budget)])

        elif report_type == "executive":
            budget = db.query(Budget).filter(Budget.project_id == project_id).first()
            milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
            avg_comp = sum(m.completion_percentage for m in milestones) / len(milestones) if milestones else 0.0
            schedules = db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
            
            writer.writerow(["EXECUTIVE MANAGEMENT KPIS"])
            writer.writerow(["Metric Name", "Metric Value"])
            writer.writerow(["Overall Milestone Progress", f"{avg_comp:.2f}%"])
            writer.writerow(["Total Budget Expended", float(budget.total_estimated_cost if budget else 0.0)])
            writer.writerow(["Active Crew Scheduled", len(schedules)])

        elif report_type == "progress":
            milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
            writer.writerow(["PROGRESS REPORTS - MILESTONES"])
            writer.writerow(["Milestone Name", "Planned End Date", "Actual End Date", "Completion %", "Status"])
            for m in milestones:
                writer.writerow([m.milestone_name, m.planned_end_date.strftime("%Y-%m-%d"), m.actual_end_date.strftime("%Y-%m-%d") if m.actual_end_date else "", float(m.completion_percentage), m.status])
                
        else:
            writer.writerow(["Empty Report"])
            
        return output.getvalue()
