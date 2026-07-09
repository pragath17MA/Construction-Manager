import os
import json
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.chat import ChatSession, ChatMessage
from app.models.project import Project, SiteImage
from app.models.budget import Budget
from app.models.material import Inventory, Material
from app.models.worker import WorkerSchedule, Attendance
from app.models.risk import Risk
from app.models.progress import Milestone
from app.models.invoice import Invoice
from app.models.image_analysis import SiteImageAnalysis
from app.services.embedding_service import EmbeddingService
from app.services.image_analysis_service import ImageAnalysisService
from app.agents.chat_agent import chat_assistant_agent

logger = logging.getLogger(__name__)

class ChatService:
    @staticmethod
    def create_session(db: Session, user_id: int, project_id: Optional[int] = None, session_name: Optional[str] = None) -> ChatSession:
        """Creates a new conversational chat session."""
        name = session_name or "New Conversation"
        if not session_name and project_id:
            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj:
                name = f"Chat: {proj.project_name}"

        session = ChatSession(
            user_id=user_id,
            project_id=project_id,
            session_name=name
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: int, user_id: int) -> ChatSession:
        """Retrieves a specific chat session with its full message log."""
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
        return session

    @staticmethod
    def list_sessions(db: Session, user_id: int, project_id: Optional[int] = None) -> List[ChatSession]:
        """Lists chat sessions for a user, optionally filtered by project."""
        query = db.query(ChatSession).filter(ChatSession.user_id == user_id)
        if project_id:
            query = query.filter(ChatSession.project_id == project_id)
        return query.order_by(ChatSession.created_at.desc()).all()

    @staticmethod
    def delete_session(db: Session, session_id: int, user_id: int) -> bool:
        """Deletes a chat session."""
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
        db.delete(session)
        db.commit()
        return True

    @staticmethod
    def _get_operational_context(db: Session, project_id: Optional[int]) -> Dict[str, Any]:
        """Aggregates all project metrics into a compact operational dictionary."""
        context = {}
        if not project_id:
            return context

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return context

        context["project_name"] = project.project_name
        context["location"] = project.location
        context["client"] = project.client_name
        context["status"] = project.status
        context["start_date"] = project.start_date.strftime("%Y-%m-%d")
        context["end_date"] = project.expected_end_date.strftime("%Y-%m-%d")
        context["budget_limit"] = float(project.budget)

        # Budget Metrics
        budget = db.query(Budget).filter(Budget.project_id == project_id).first()
        if budget:
            context["estimated_cost"] = float(budget.total_estimated_cost)
            context["optimized_cost"] = float(budget.total_optimized_cost or budget.total_estimated_cost)
            context["currency"] = budget.currency
            context["budget_items_count"] = len(budget.items) if budget.items else 0
        else:
            context["estimated_cost"] = 0.0
            context["optimized_cost"] = 0.0

        # Milestone Progress
        milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
        if milestones:
            avg_comp = sum(float(m.completion_percentage) for m in milestones) / len(milestones)
            context["overall_completion"] = round(avg_comp, 2)
            context["milestones_count"] = len(milestones)
            
            today = date.today()
            variance = 0
            for m in milestones:
                if m.completion_percentage < 100.0 and m.planned_end_date and m.planned_end_date < today:
                    variance += (today - m.planned_end_date).days
            context["variance_days"] = variance
        else:
            context["overall_completion"] = 0.0
            context["variance_days"] = 0

        # Workers & Attendance
        schedules = db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
        context["active_workers_count"] = len(schedules)
        context["roles"] = list(set([s.worker.role_title for s in schedules if s.worker]))
        
        # Materials & Inventory
        project_materials = db.query(Material).filter(Material.project_id == project_id).all()
        mat_list = []
        for mat in project_materials:
            inv = db.query(Inventory).filter(Inventory.material_name == mat.material_name).first()
            mat_list.append({
                "material_name": mat.material_name,
                "quantity_needed": float(mat.quantity),
                "available": float(inv.quantity_available) if inv else 0.0,
                "unit": mat.unit,
                "status": "Shortage" if not inv or float(inv.quantity_available) < float(mat.quantity) else "Available"
            })
        context["materials"] = mat_list

        # Safety & Image Audits
        analyses = db.query(SiteImageAnalysis).filter(SiteImageAnalysis.project_id == project_id).all()
        all_hazards = []
        for analysis in analyses:
            if analysis.safety_issues:
                try:
                    issues = json.loads(analysis.safety_issues)
                    if isinstance(issues, list):
                        all_hazards.extend(issues)
                except Exception:
                    all_hazards.append(analysis.safety_issues)
        context["safety_issues"] = list(set(all_hazards))
        context["visual_inspections_count"] = len(analyses)

        # Invoices
        invoices = db.query(Invoice).filter(Invoice.project_id == project_id).all()
        context["invoices_count"] = len(invoices)
        context["unpaid_invoices_count"] = sum(1 for inv in invoices if inv.status == "Pending")
        context["total_invoice_amount"] = sum(float(inv.total_amount) for inv in invoices)

        # Risks & Weather
        risk = db.query(Risk).filter(Risk.project_id == project_id).first()
        if risk:
            context["risk_score"] = float(risk.risk_score)
            context["delay_probability"] = float(risk.delay_probability)
            context["weather_risk"] = risk.weather_risk_severity
            context["labor_risk"] = risk.worker_risk_severity
        else:
            context["risk_score"] = 0.0
            context["delay_probability"] = 0.0

        return context

    @staticmethod
    def process_chat_query(
        db: Session,
        user_id: int,
        session_id: int,
        query_text: str,
        image_path: Optional[str] = None
    ) -> ChatMessage:
        """
        Main LangGraph chat logic.
        Validates access, gathers contexts, performs drawings RAG lookup if needed, and saves history.
        """
        # 1. Fetch and validate session access
        session = ChatService.get_session(db, session_id, user_id)
        project_id = session.project_id

        # 2. Compile chat memory context
        chat_history = [
            {"sender": msg.sender, "text": msg.message_text}
            for msg in session.messages[-10:] # last 10 turns for memory window
        ]

        # 3. Trigger LangGraph first routing node
        routing_state = {
            "user_id": user_id,
            "project_id": project_id,
            "session_id": session_id,
            "query": query_text,
            "chat_history": chat_history,
            "context_data": {},
            "vector_context": "",
            "image_analysis_context": "",
            "response": "",
            "errors": []
        }
        
        try:
            routing_res = chat_assistant_agent.invoke(routing_state)
            needs_rag = routing_res.get("context_data", {}).get("needs_rag", False)
        except Exception as e:
            logger.error(f"Routing node query analyze failed: {e}")
            needs_rag = False

        # 4. Gather operational database summaries
        context_data = ChatService._get_operational_context(db, project_id)

        # 5. Gather ChromaDB drawing vector context if drawing specification is queried
        vector_context = ""
        if needs_rag and project_id:
            try:
                vector_results = EmbeddingService.query_similarity(
                    collection_name="construction_drawings",
                    query_text=query_text,
                    limit=3,
                    where_filter={"project_id": project_id}
                )
                chunks = [res["text"] for res in vector_results]
                vector_context = "\n---\n".join(chunks)
            except Exception as e:
                logger.error(f"Failed to query drawings vector DB: {e}")

        # 6. Gather image analysis context if an image is uploaded in current query
        image_analysis_context = ""
        if image_path and project_id:
            try:
                # 6.1 Register SiteImage
                site_img = SiteImage(
                    project_id=project_id,
                    image_path=image_path,
                    capture_date=date.today()
                )
                db.add(site_img)
                db.commit()
                db.refresh(site_img)
                
                # 6.2 Trigger visual analysis service
                analysis = ImageAnalysisService.analyze_image(db, project_id, site_img.id)
                
                # 6.3 Format image findings summary
                image_analysis_context = (
                    f"Uploaded image ID: {site_img.id}. "
                    f"AI Construction Stage detected: {analysis.construction_stage}. "
                    f"Detections: {analysis.safety_issues}. "
                    f"AI Recommendations: {analysis.recommendations}."
                )
            except Exception as e:
                logger.error(f"Failed to analyze query visual image attachment: {e}")
                image_analysis_context = "Image upload failed verification checks."

        # 7. Invoke LangGraph synthesis node with full context
        synthesis_state = {
            "user_id": user_id,
            "project_id": project_id,
            "session_id": session_id,
            "query": query_text,
            "chat_history": chat_history,
            "context_data": context_data,
            "vector_context": vector_context,
            "image_analysis_context": image_analysis_context,
            "response": "",
            "errors": []
        }

        try:
            final_res = chat_assistant_agent.invoke(synthesis_state)
            response_text = final_res.get("response", "I could not formulate an answer.")
        except Exception as e:
            logger.error(f"Synthesis answer generation node failed: {e}")
            response_text = "I encountered an error during conversation synthesis."

        # 8. Save user and assistant message records to db
        user_msg = ChatMessage(
            session_id=session_id,
            sender="user",
            message_text=query_text
        )
        assistant_msg = ChatMessage(
            session_id=session_id,
            sender="assistant",
            message_text=response_text
        )
        
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        return assistant_msg
