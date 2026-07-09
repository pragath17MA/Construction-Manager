import os
import json
import logging
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class RiskAgentState(TypedDict):
    project_id: int
    weather_data: Dict[str, Any]
    material_status: Dict[str, Any]
    worker_availability: Dict[str, Any]
    equipment_status: Dict[str, Any]
    budget_status: Dict[str, Any]
    progress_status: Dict[str, Any]
    
    # Outputs
    composite_risk_score: int
    delay_probability: float
    severities: Dict[str, str]
    ai_recommendations: str
    executive_summary: str
    errors: List[str]

# 1. Weather Analysis Node
def weather_analysis_node(state: RiskAgentState) -> Dict[str, Any]:
    severities = state.get("severities", {})
    weather = state.get("weather_data", {})
    
    precipitation = float(weather.get("precipitation", 0.0))
    wind_speed = float(weather.get("wind_speed", 0.0))
    alerts = weather.get("alerts", "")
    
    if "storm" in alerts.lower() or "cyclone" in alerts.lower() or precipitation > 80.0:
        weather_sev = "Critical"
    elif precipitation > 40.0 or wind_speed > 50.0:
        weather_sev = "High"
    elif precipitation > 15.0 or wind_speed > 25.0:
        weather_sev = "Medium"
    else:
        weather_sev = "Low"
        
    severities["weather"] = weather_sev
    return {"severities": severities}

# 2. Material Status Node
def material_status_node(state: RiskAgentState) -> Dict[str, Any]:
    severities = state.get("severities", {})
    mat = state.get("material_status", {})
    
    shortages_count = len(mat.get("low_stock_warnings", []))
    pending_pos = len(mat.get("pending_purchase_orders", []))
    
    if shortages_count > 4:
        mat_sev = "Critical"
        sup_sev = "Critical"
    elif shortages_count > 1:
        mat_sev = "High"
        sup_sev = "High"
    elif pending_pos > 0:
        mat_sev = "Medium"
        sup_sev = "Medium"
    else:
        mat_sev = "Low"
        sup_sev = "Low"
        
    severities["material"] = mat_sev
    severities["supplier"] = sup_sev
    return {"severities": severities}

# 3. Worker Availability Node
def worker_availability_node(state: RiskAgentState) -> Dict[str, Any]:
    severities = state.get("severities", {})
    work = state.get("worker_availability", {})
    
    shortages_count = len(work.get("shortage_warnings", []))
    active_headcount = int(work.get("active_workers_count", 0))
    
    if shortages_count > 3 or active_headcount == 0:
        worker_sev = "Critical"
    elif shortages_count > 0:
        worker_sev = "High"
    elif active_headcount < 5:
        worker_sev = "Medium"
    else:
        worker_sev = "Low"
        
    severities["worker"] = worker_sev
    return {"severities": severities}

# 4. Equipment Status Node
def equipment_status_node(state: RiskAgentState) -> Dict[str, Any]:
    severities = state.get("severities", {})
    equip = state.get("equipment_status", {})
    
    failures = int(equip.get("failures_count", 0))
    maintenance = int(equip.get("maintenance_count", 0))
    
    if failures > 2:
        equip_sev = "Critical"
        safety_sev = "High"
    elif failures > 0 or maintenance > 3:
        equip_sev = "High"
        safety_sev = "Medium"
    elif maintenance > 0:
        equip_sev = "Medium"
        safety_sev = "Low"
    else:
        equip_sev = "Low"
        safety_sev = "Low"
        
    severities["equipment"] = equip_sev
    severities["safety"] = safety_sev
    return {"severities": severities}

# 5. Budget Status Node
def budget_status_node(state: RiskAgentState) -> Dict[str, Any]:
    severities = state.get("severities", {})
    budget = state.get("budget_status", {})
    
    total = float(budget.get("total_budget", 1.0))
    spent = float(budget.get("budget_spent", 0.0))
    
    ratio = spent / total if total > 0 else 0.0
    
    if ratio > 1.10:
        budget_sev = "Critical"
    elif ratio > 0.90:
        budget_sev = "High"
    elif ratio > 0.50:
        budget_sev = "Medium"
    else:
        budget_sev = "Low"
        
    severities["budget"] = budget_sev
    return {"severities": severities}

# 6. Progress Status Node
def progress_status_node(state: RiskAgentState) -> Dict[str, Any]:
    severities = state.get("severities", {})
    prog = state.get("progress_status", {})
    
    variance = int(prog.get("variance_days", 0))
    completion = float(prog.get("overall_completion_percentage", 0.0))
    
    if variance > 45:
        timeline_sev = "Critical"
    elif variance > 15:
        timeline_sev = "High"
    elif variance > 5 or completion < 10.0:
        timeline_sev = "Medium"
    else:
        timeline_sev = "Low"
        
    severities["timeline"] = timeline_sev
    return {"severities": severities}

# 7. Composite Risk Scoring Node
def risk_prediction_node(state: RiskAgentState) -> Dict[str, Any]:
    severities = state.get("severities", {})
    
    severity_weights = {
        "Critical": 25,
        "High": 15,
        "Medium": 8,
        "Low": 2
    }
    
    score = 0
    for cat in ["weather", "material", "budget", "worker", "equipment", "supplier", "safety", "timeline"]:
        sev = severities.get(cat, "Low")
        score += severity_weights.get(sev, 2)
        
    # Cap composite score at 100
    composite_score = min(100, max(0, score))
    return {"composite_risk_score": composite_score}

# 8. Delay Prediction Probability Node
def delay_prediction_node(state: RiskAgentState) -> Dict[str, Any]:
    score = state.get("composite_risk_score", 0)
    
    # Probability defaults to composite score factor, but shifts with timeline risk weight
    timeline_sev = state.get("severities", {}).get("timeline", "Low")
    multiplier = 1.0
    if timeline_sev == "Critical":
        multiplier = 1.25
    elif timeline_sev == "High":
        multiplier = 1.15
    elif timeline_sev == "Medium":
        multiplier = 1.05
        
    prob = float(score) * multiplier
    delay_prob = min(100.00, max(0.00, prob))
    return {"delay_probability": round(delay_prob, 2)}

# 9. AI Recommendations Node (Groq LLM)
def ai_recommendation_node(state: RiskAgentState) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY", "")
    
    prompt = f"""
    You are an expert AI Construction Risk Officer and Project Management Consultant.
    We have run a comprehensive multi-factor risk assessment on a construction project:

    Project ID: {state.get('project_id')}
    Calculated Composite Risk Score: {state.get('composite_risk_score')} / 100
    Predicted Project Delay Probability: {state.get('delay_probability')}%

    Calculated Risk Category Severities:
    - Weather Delays Risk: {state['severities'].get('weather')}
    - Material Shortages Risk: {state['severities'].get('material')}
    - Budget Overruns Risk: {state['severities'].get('budget')}
    - Worker Shortages Risk: {state['severities'].get('worker')}
    - Equipment Failures Risk: {state['severities'].get('equipment')}
    - Supplier Delays Risk: {state['severities'].get('supplier')}
    - Safety Incidents Risk: {state['severities'].get('safety')}
    - Timeline Delay Risk: {state['severities'].get('timeline')}

    Input Status Data:
    - Weather alert flags: {json.dumps(state.get('weather_data'))}
    - Materials stock warnings: {json.dumps(state.get('material_status'))}
    - Workforce shortage flags: {json.dumps(state.get('worker_availability'))}
    - Cost parameters: {json.dumps(state.get('budget_status'))}
    - Milestone delay parameters: {json.dumps(state.get('progress_status'))}

    Generate a detailed Executive Risk Summary (2-3 paragraphs explaining the root causes of the flagged risks) 
    and provide 3-5 specific, highly actionable AI Mitigation Suggestions in Markdown format.
    """

    if not api_key:
        logger.warning("GROQ_API_KEY environment variable not found. Using sandbox fallback optimization.")
        summary = (
            f"The composite risk index is evaluated at {state.get('composite_risk_score')}/100. "
            f"Primary risk drivers are weather impacts ({state['severities'].get('weather')}) and timeline constraints ({state['severities'].get('timeline')}). "
            "Site managers are advised to monitor heavy rainfall alerts and cross-train concrete crews."
        )
        recommendations = (
            "1. Adjust concreting windows to prevent rain washout.\n"
            "2. Establish secondary local steel supplier contracts to circumvent logistics bottlenecks.\n"
            "3. Optimize machinery check intervals to lower maintenance downtime risks."
        )
        return {"executive_summary": summary, "ai_recommendations": recommendations}

    try:
        chat = ChatGroq(
            temperature=0.25,
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile"
        )
        msg = chat.invoke([HumanMessage(content=prompt)])
        
        # Split output into summary and recommendations
        content = msg.content
        if "Mitigation" in content:
            parts = content.split("Mitigation", 1)
            summary = parts[0].strip()
            recs = "Mitigation" + parts[1]
        else:
            summary = content
            recs = "Review site logistics plan and prepare contingency rosters."
            
        return {"executive_summary": summary, "ai_recommendations": recs}
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return {
            "executive_summary": "Risk assessment compiled successfully. Deep AI recommendations narrative failed due to model limits.",
            "ai_recommendations": "1. Set up drainage pumps for weather limits.\n2. Expand material safety stock reserves."
        }

# Define State Machine Graph
workflow = StateGraph(RiskAgentState)

workflow.add_node("analyze_weather", weather_analysis_node)
workflow.add_node("analyze_materials", material_status_node)
workflow.add_node("analyze_workers", worker_availability_node)
workflow.add_node("analyze_equipment", equipment_status_node)
workflow.add_node("analyze_budget", budget_status_node)
workflow.add_node("analyze_progress", progress_status_node)
workflow.add_node("predict_risks", risk_prediction_node)
workflow.add_node("predict_delays", delay_prediction_node)
workflow.add_node("generate_ai_mitigations", ai_recommendation_node)

workflow.set_entry_point("analyze_weather")

workflow.add_edge("analyze_weather", "analyze_materials")
workflow.add_edge("analyze_materials", "analyze_workers")
workflow.add_edge("analyze_workers", "analyze_equipment")
workflow.add_edge("analyze_equipment", "analyze_budget")
workflow.add_edge("analyze_budget", "analyze_progress")
workflow.add_edge("analyze_progress", "predict_risks")
workflow.add_edge("predict_risks", "predict_delays")
workflow.add_edge("predict_delays", "generate_ai_mitigations")
workflow.add_edge("generate_ai_mitigations", END)

risk_prediction_agent = workflow.compile()
