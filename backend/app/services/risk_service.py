import os
import json
import urllib.request
import urllib.parse
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from fastapi import HTTPException

from app.models.project import Project
from app.models.risk import Risk, RiskHistory, WeatherData, DelayPrediction
from app.models.material import Inventory, PurchaseOrder
from app.models.worker import Worker, WorkerSchedule, LeaveRequest
from app.models.progress import Milestone
from app.agents.risk_agent import risk_prediction_agent

logger = logging.getLogger(__name__)

class RiskService:
    @staticmethod
    def get_live_weather(db: Session, project_id: int, location: str) -> WeatherData:
        """
        Fetches live weather data from OpenWeather. Caches it in DB for 30 minutes.
        Falls back to a sandbox weather profile if API calls fail or credentials are missing.
        """
        # Check cache
        cache_limit = datetime.now() - timedelta(minutes=30)
        cached = db.query(WeatherData).filter(
            WeatherData.project_id == project_id,
            WeatherData.cached_at >= cache_limit
        ).order_by(WeatherData.cached_at.desc()).first()

        if cached:
            return cached

        # Sandbox defaults
        temp = Decimal("28.00")
        wind = Decimal("10.00")
        precip = Decimal("0.00")
        humid = Decimal("60.00")
        desc = "Partly Cloudy"
        alerts = ""

        api_key = os.getenv("OPENWEATHER_API_KEY", "")
        if api_key:
            try:
                # Encode location parameter
                safe_loc = urllib.parse.quote(location)
                url = f"https://api.openweathermap.org/data/2.5/weather?q={safe_loc}&appid={api_key}&units=metric"
                
                # Fetch JSON
                req = urllib.request.Request(url, headers={"User-Agent": "APEXBuild/1.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    
                    temp = Decimal(str(data["main"].get("temp", 28.00)))
                    wind = Decimal(str(data["wind"].get("speed", 10.00)))
                    humid = Decimal(str(data["main"].get("humidity", 60.00)))
                    desc = data["weather"][0].get("description", "Clear")
                    
                    # Rain key precipitation check
                    rain = data.get("rain", {})
                    precip = Decimal(str(rain.get("1h", 0.00)))
                    
                    # Check code alerts
                    if data["main"].get("temp", 28.00) > 42.0:
                        alerts = "Extreme Heatwave Warning"
                    elif rain.get("1h", 0.0) > 30.0:
                        alerts = "Heavy Downpour Flood Warning"
            except Exception as e:
                logger.error(f"Live Weather API lookup failed: {e}. Falling back to sandbox.")
                alerts = "Weather API fallback mode active."

        # Update cache
        db_weather = WeatherData(
            project_id=project_id,
            location=location,
            temperature=temp,
            wind_speed=wind,
            precipitation=precip,
            humidity=humid,
            weather_description=desc,
            alerts=alerts,
            cached_at=datetime.now()
        )
        db.add(db_weather)
        db.commit()
        db.refresh(db_weather)
        return db_weather

    @staticmethod
    def analyze_project_risks(db: Session, project_id: int) -> Dict[str, Any]:
        """
        Gathers live stats, invokes the Risk agent, and saves risk records.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        # 1. Weather Data
        weather = RiskService.get_live_weather(db, project_id, project.location)
        weather_dict = {
            "temperature": float(weather.temperature),
            "wind_speed": float(weather.wind_speed),
            "precipitation": float(weather.precipitation),
            "humidity": float(weather.humidity),
            "alerts": weather.alerts or ""
        }

        # 2. Material Stock status
        inventory_rows = db.query(Inventory).all()
        # Compile warnings for stock
        low_stock = []
        for i in inventory_rows:
            net = float(i.quantity_available) - float(i.quantity_reserved)
            if net < 100.0: # arbitrary low threshold
                low_stock.append(f"Low Stock: {i.material_name}")
                
        pending_pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.project_id == project_id,
            PurchaseOrder.status == "Pending"
        ).all()
        
        material_dict = {
            "low_stock_warnings": low_stock,
            "pending_purchase_orders": [p.id for p in pending_pos]
        }

        # 3. Worker Availability status
        workers = db.query(Worker).filter(Worker.active == True).all()
        schedules = db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
        leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "Approved").all()
        
        shortages = []
        if len(schedules) < 3:
            shortages.append("Roster headcount shortage: understaffed shift allocations.")
            
        worker_dict = {
            "active_workers_count": len(workers),
            "shortage_warnings": shortages
        }

        # 4. Equipment failures status
        failures_count = 0
        maintenance_count = 0
        from app.models.budget import EquipmentCost
        equip_items = db.query(EquipmentCost).all()
        for eq in equip_items:
            if eq.days_used > 5:
                maintenance_count += 1
            if eq.total_cost > 100000:
                failures_count = max(failures_count, 1)

        equipment_dict = {
            "failures_count": failures_count,
            "maintenance_count": maintenance_count
        }

        # 5. Budget Cost Overrun status
        from app.models.budget import Budget
        budget_row = db.query(Budget).filter(Budget.project_id == project_id).first()
        total_budget = float(project.budget)
        spent_so_far = 0.0
        if budget_row:
            spent_so_far = float(budget_row.total_estimated_cost)
            
        budget_dict = {
            "total_budget": total_budget,
            "budget_spent": spent_so_far
        }

        # 6. Progress and timeline delay status
        milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
        variance_days = 0
        overall_completion = 0.0
        
        if milestones:
            pct_sum = sum(float(m.completion_percentage) for m in milestones)
            overall_completion = pct_sum / len(milestones)
            
            # Sum up positive variance days (i.e. planned end date has passed but completion < 100)
            today = datetime.now().date()
            for m in milestones:
                if m.completion_percentage < 100.0 and m.planned_end_date < today:
                    variance_days += (today - m.planned_end_date).days

        progress_dict = {
            "variance_days": variance_days,
            "overall_completion_percentage": overall_completion
        }

        # 7. Run LangGraph Risk Prediction Agent
        state = {
            "project_id": project_id,
            "weather_data": weather_dict,
            "material_status": material_dict,
            "worker_availability": worker_dict,
            "equipment_status": equipment_dict,
            "budget_status": budget_dict,
            "progress_status": progress_dict,
            "composite_risk_score": 0,
            "delay_probability": 0.0,
            "severities": {},
            "ai_recommendations": "",
            "executive_summary": "",
            "errors": []
        }

        result = risk_prediction_agent.invoke(state)

        # Clear old risk record for project to refresh current assessment
        db.query(Risk).filter(Risk.project_id == project_id).delete()
        
        # Save new current risk
        risk = Risk(
            project_id=project_id,
            risk_score=result["composite_risk_score"],
            delay_probability=Decimal(str(result["delay_probability"])),
            executive_summary=result["executive_summary"],
            weather_risk_severity=result["severities"].get("weather", "Low"),
            material_risk_severity=result["severities"].get("material", "Low"),
            budget_risk_severity=result["severities"].get("budget", "Low"),
            worker_risk_severity=result["severities"].get("worker", "Low"),
            equipment_risk_severity=result["severities"].get("equipment", "Low"),
            supplier_risk_severity=result["severities"].get("supplier", "Low"),
            safety_risk_severity=result["severities"].get("safety", "Low"),
            timeline_risk_severity=result["severities"].get("timeline", "Low"),
            ai_mitigation_suggestions=result["ai_recommendations"]
        )
        db.add(risk)

        # Append to Audit Risk History list
        history = RiskHistory(
            project_id=project_id,
            risk_score=result["composite_risk_score"],
            delay_probability=Decimal(str(result["delay_probability"])),
            executive_summary=result["executive_summary"]
        )
        db.add(history)

        # Update Delay Predictions model
        db.query(DelayPrediction).filter(DelayPrediction.project_id == project_id).delete()
        predicted_days = int(variance_days * 1.2) if variance_days > 0 else int(result["composite_risk_score"] / 10)
        
        delay_pred = DelayPrediction(
            project_id=project_id,
            probability=Decimal(str(result["delay_probability"])),
            predicted_delay_days=predicted_days,
            variance_days=variance_days,
            root_causes=f"Category risks: Weather={risk.weather_risk_severity}, Timeline={risk.timeline_risk_severity}.",
            recovery_recommendations=result["ai_recommendations"]
        )
        db.add(delay_pred)

        db.commit()
        db.refresh(risk)
        db.refresh(delay_pred)

        return {
            "risk": risk,
            "delay_prediction": delay_pred,
            "weather": weather
        }

    @staticmethod
    def get_current_risk(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves active risk scores."""
        risk = db.query(Risk).filter(Risk.project_id == project_id).first()
        delay = db.query(DelayPrediction).filter(DelayPrediction.project_id == project_id).first()
        weather = db.query(WeatherData).filter(WeatherData.project_id == project_id).order_by(WeatherData.cached_at.desc()).first()
        
        if not risk:
            return None
            
        return {
            "risk": risk,
            "delay_prediction": delay,
            "weather": weather
        }

    @staticmethod
    def get_risk_history(db: Session, project_id: int, skip: int = 0, limit: int = 10) -> List[RiskHistory]:
        """Gets pagination lists of historical audits."""
        return db.query(RiskHistory).filter(RiskHistory.project_id == project_id).order_by(RiskHistory.created_at.desc()).offset(skip).limit(limit).all()
