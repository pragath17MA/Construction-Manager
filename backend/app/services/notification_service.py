import os
import time
import logging
import json
import threading
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models.notification import NotificationLog
from app.models.project import Project, ProjectMember
from app.models.budget import Budget
from app.models.material import Material, Inventory
from app.models.worker import WorkerSchedule
from app.models.risk import Risk, WeatherData
from app.models.progress import Milestone
from app.models.image_analysis import SiteImageAnalysis

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_email(recipient: str, subject: str, body: str) -> bool:
        """Simulates sending an Email notification, logging details to output."""
        logger.info(f"[NOTIFY] [EMAIL] To: {recipient} | Subject: {subject} | Body: {body[:150]}...")
        return True

    @staticmethod
    def send_whatsapp(recipient_phone: str, message: str) -> bool:
        """Simulates sending a WhatsApp alert template, logging details to output."""
        logger.info(f"[NOTIFY] [WHATSAPP] To: {recipient_phone} | Message: {message[:150]}...")
        return True

    @staticmethod
    def send_push(user_id: int, title: str, body: str) -> bool:
        """Simulates dispatching a Mobile/Browser Push Notification, logging details to output."""
        logger.info(f"[NOTIFY] [PUSH] User: {user_id} | Title: {title} | Body: {body[:150]}...")
        return True

    @staticmethod
    def trigger_operational_alert(db: Session, project_id: int, user_id: int, alert_type: str, message: str, recipient_email: str, recipient_phone: str) -> List[NotificationLog]:
        """Dispatches an alert to a user through all 3 notification channels and logs them in DB."""
        logs = []
        
        # 1. Email Channel
        email_sent = NotificationService.send_email(
            recipient=recipient_email,
            subject=f"APEXBuild Critical Alert: {alert_type}",
            body=message
        )
        log_email = NotificationLog(
            project_id=project_id,
            user_id=user_id,
            alert_type=alert_type,
            channel="Email",
            recipient=recipient_email,
            message=message,
            status="Sent" if email_sent else "Failed"
        )
        db.add(log_email)
        logs.append(log_email)

        # 2. WhatsApp Channel
        wa_sent = NotificationService.send_whatsapp(
            recipient_phone=recipient_phone,
            message=f"*{alert_type} Alert* on project: {message}"
        )
        log_wa = NotificationLog(
            project_id=project_id,
            user_id=user_id,
            alert_type=alert_type,
            channel="WhatsApp",
            recipient=recipient_phone,
            message=message,
            status="Sent" if wa_sent else "Failed"
        )
        db.add(log_wa)
        logs.append(log_wa)

        # 3. Push Channel
        push_sent = NotificationService.send_push(
            user_id=user_id,
            title=alert_type,
            body=message
        )
        log_push = NotificationLog(
            project_id=project_id,
            user_id=user_id,
            alert_type=alert_type,
            channel="Push",
            recipient=f"push_token_user_{user_id}",
            message=message,
            status="Sent" if push_sent else "Failed"
        )
        db.add(log_push)
        logs.append(log_push)

        db.commit()
        return logs

    @classmethod
    def check_and_trigger_alerts(cls, db: Session):
        """Scans all modules database records for threat alerts and sends notifications to team members."""
        projects = db.query(Project).all()
        if not projects:
            return

        today = date.today()
        cooldown_time = datetime.now() - timedelta(hours=24)

        for proj in projects:
            project_id = proj.id
            project_name = proj.project_name
            
            # Fetch assigned users (e.g. PMs or Creators)
            members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
            user_list = [m.user for m in members if m.user]
            if proj.creator and proj.creator not in user_list:
                user_list.append(proj.creator)
                
            if not user_list:
                continue

            alerts_to_send = []

            # 1. Budget Alert
            budget = db.query(Budget).filter(Budget.project_id == project_id).first()
            if budget and float(budget.total_estimated_cost) > float(proj.budget):
                alerts_to_send.append({
                    "type": "Budget Exceeded",
                    "msg": f"Budget alert for {project_name}: Total estimated cost (INR {float(budget.total_estimated_cost):,.2f}) exceeds the project limit (INR {float(proj.budget):,.2f})."
                })

            # 2. Material Shortage Alert
            materials = db.query(Material).filter(Material.project_id == project_id).all()
            inventory_rows = db.query(Inventory).all()
            inv_map = {i.material_name: float(i.quantity_available) for i in inventory_rows}
            
            shortage_names = []
            for mat in materials:
                available = inv_map.get(mat.material_name, 0.0)
                if available < float(mat.quantity):
                    shortage_names.append(mat.material_name)
                    
            if shortage_names:
                alerts_to_send.append({
                    "type": "Material Shortage",
                    "msg": f"Supply chain shortage for {project_name}: The following materials are low in stock: {', '.join(shortage_names)}."
                })

            # 3. Worker Shortage Alert
            schedules = db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
            if len(schedules) < 2:
                alerts_to_send.append({
                    "type": "Worker Shortage",
                    "msg": f"Workforce deficit alert for {project_name}: Active workers roster count ({len(schedules)}) is below target limit."
                })

            # 4. Delay Prediction Alert
            risk = db.query(Risk).filter(Risk.project_id == project_id).first()
            if risk and float(risk.delay_probability) > 50.0:
                alerts_to_send.append({
                    "type": "Delay Prediction",
                    "msg": f"Schedule risk alert for {project_name}: AI models forecast a {float(risk.delay_probability):.1f}% timeline delay probability."
                })

            # 5. Weather Warning Alert
            weather = db.query(WeatherData).filter(WeatherData.project_id == project_id).first()
            if weather and weather.alerts and weather.alerts.strip():
                alerts_to_send.append({
                    "type": "Weather Warning",
                    "msg": f"Weather advisory alert for {project_name}: Active storm warning: '{weather.alerts}'."
                })

            # 6. Safety Violation Alert
            analyses = db.query(SiteImageAnalysis).filter(SiteImageAnalysis.project_id == project_id).all()
            safety_count = 0
            for a in analyses:
                if a.safety_issues:
                    try:
                        issues = json.loads(a.safety_issues)
                        safety_count += len(issues) if isinstance(issues, list) else 1
                    except Exception:
                        safety_count += 1
            if safety_count > 0:
                alerts_to_send.append({
                    "type": "Safety Violation",
                    "msg": f"PPE safety alert for {project_name}: {safety_count} visual compliance hazards detected during audits."
                })

            # 7. Project Completion Alert
            milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
            if milestones and all(m.completion_percentage >= 100.0 for m in milestones):
                alerts_to_send.append({
                    "type": "Project Completion",
                    "msg": f"Milestone complete alert for {project_name}: All planning phases have reached 100% completion."
                })

            # Dispatch qualifying alerts to members
            for alert in alerts_to_send:
                alert_type = alert["type"]
                message = alert["msg"]
                
                for user in user_list:
                    # Cooldown check: has this alert type been sent to this user in the past 24 hours?
                    already_sent = db.query(NotificationLog).filter(
                        NotificationLog.project_id == project_id,
                        NotificationLog.user_id == user.id,
                        NotificationLog.alert_type == alert_type,
                        NotificationLog.created_at >= cooldown_time
                    ).first()
                    
                    if not already_sent:
                        cls.trigger_operational_alert(
                            db=db,
                            project_id=project_id,
                            user_id=user.id,
                            alert_type=alert_type,
                            message=message,
                            recipient_email=user.email,
                            recipient_phone="9999999999" # stub phone
                        )

class BackgroundNotificationScheduler:
    _thread = None
    _running = False
    
    @classmethod
    def start(cls):
        """Starts background notification checks loop in a daemon thread."""
        if cls._thread is None:
            cls._running = True
            cls._thread = threading.Thread(target=cls._loop, daemon=True)
            cls._thread.start()
            logger.info("Background Notification Scheduler daemon started successfully.")
            
    @classmethod
    def stop(cls):
        """Halts the scheduler daemon loop."""
        cls._running = False
        if cls._thread:
            cls._thread.join(timeout=1.0)
            cls._thread = None
            logger.info("Background Notification Scheduler daemon stopped.")
            
    @classmethod
    def _loop(cls):
        # Run checker loop every 10 seconds during dev/test to react fast, 60s in prod
        while cls._running:
            try:
                from app.core.database import SessionLocal
                db = SessionLocal()
                try:
                    NotificationService.check_and_trigger_alerts(db)
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in Notification Scheduler loop iteration: {e}")
            
            # Bounded polling sleep
            for _ in range(10):
                if not cls._running:
                    break
                time.sleep(1.0)
