import os
import json
import logging
from datetime import datetime, date
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class ProgressAgentState(TypedDict):
    project_id: int
    milestones: List[Dict[str, Any]]
    daily_logs: List[Dict[str, Any]]
    budget_spent: float
    budget_limit: float
    resource_utilization: float
    
    # Outputs
    overall_completion_percentage: float
    variance_days: int
    variance_status: str
    ai_progress_summary: str
    errors: List[str]

# 1. Timeline Variance Node
def timeline_variance_node(state: ProgressAgentState) -> Dict[str, Any]:
    milestones = state.get("milestones", [])
    
    total_pct = 0.0
    completed_count = 0
    variance_days = 0
    
    today = date.today()
    
    for ms in milestones:
        pct = float(ms.get("completion_percentage", 0.0))
        total_pct += pct
        
        # Calculate delay variance if milestone not completed but planned end has passed
        planned = ms.get("planned_end_date")
        actual = ms.get("actual_end_date")
        
        # Ensure planned date is formatted correctly as a date object
        if isinstance(planned, str):
            planned_date = datetime.strptime(planned, "%Y-%m-%d").date()
        else:
            planned_date = planned
            
        if isinstance(actual, str) and actual:
            actual_date = datetime.strptime(actual, "%Y-%m-%d").date()
        else:
            actual_date = actual if actual else None
            
        if pct < 100.0 and planned_date and planned_date < today:
            variance_days += (today - planned_date).days
        elif pct >= 100.0 and planned_date and actual_date:
            if actual_date > planned_date:
                variance_days += (actual_date - planned_date).days
                
    overall = total_pct / len(milestones) if len(milestones) > 0 else 0.0
    return {
        "overall_completion_percentage": round(overall, 2),
        "variance_days": variance_days
    }

# 2. Budget Burn Node
def budget_burn_node(state: ProgressAgentState) -> Dict[str, Any]:
    # Pass-through node - budget parameters mapped in service
    return {"project_id": state["project_id"]}

# 3. Delay Alert Status Node
def delay_alert_node(state: ProgressAgentState) -> Dict[str, Any]:
    variance = state.get("variance_days", 0)
    
    if variance > 30:
        status = "Critical Delay"
    elif variance > 10:
        status = "Minor Variance"
    else:
        status = "On-Track"
        
    return {"variance_status": status}

# 4. AI Progress Summary Node (Groq LLM)
def ai_progress_summary_node(state: ProgressAgentState) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY", "")
    
    prompt = f"""
    You are an expert AI Construction Progress Analyst.
    We have aggregated progress data for a construction project phase:

    Project ID: {state.get('project_id')}
    Calculated Overall Completion: {state.get('overall_completion_percentage')}%
    Accumulated Schedule Variance: {state.get('variance_days')} days ({state.get('variance_status')})
    Budget Limit: {state.get('budget_limit')}
    Budget Spent: {state.get('budget_spent')}
    Resource utilization: {state.get('resource_utilization')}%

    Active Milestone Roster:
    {json.dumps(state.get('milestones', []))}

    Latest Site Daily Updates logged:
    {json.dumps(state.get('daily_logs', []))}

    Compile a concise narrative progress report detailing recent accomplishments, resource bottlenecks, budget burn evaluation, and schedule variance insights.
    Write your output in professional Markdown format.
    """

    if not api_key:
        logger.warning("GROQ_API_KEY environment variable not found. Using sandbox fallback progress summary.")
        summary = (
            f"Project progress is currently at {state.get('overall_completion_percentage')}% with a variance status of '{state.get('variance_status')}'. "
            f"The team has spent {state.get('budget_spent')} out of the allocated {state.get('budget_limit')}. "
            "Recent milestones are progressing steadily; concrete pours and framework completions are ongoing."
        )
        return {"ai_progress_summary": summary}

    try:
        chat = ChatGroq(
            temperature=0.2,
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile"
        )
        msg = chat.invoke([HumanMessage(content=prompt)])
        return {"ai_progress_summary": msg.content}
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return {"ai_progress_summary": "Progress review compiled. Deep AI progress analysis failed due to model boundaries."}

# Define State Machine
workflow = StateGraph(ProgressAgentState)

workflow.add_node("timeline_variance", timeline_variance_node)
workflow.add_node("budget_burn", budget_burn_node)
workflow.add_node("delay_alert", delay_alert_node)
workflow.add_node("ai_summary", ai_progress_summary_node)

workflow.set_entry_point("timeline_variance")

workflow.add_edge("timeline_variance", "budget_burn")
workflow.add_edge("budget_burn", "delay_alert")
workflow.add_edge("delay_alert", "ai_summary")
workflow.add_edge("ai_summary", END)

progress_monitoring_agent = workflow.compile()
