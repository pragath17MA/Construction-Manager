import os
import json
import logging
from datetime import datetime
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class WorkerAgentState(TypedDict):
    project_id: int
    start_date: str # "YYYY-MM-DD"
    end_date: str # "YYYY-MM-DD"
    required_roles: List[str]
    
    # Input Pools
    workers_pool: List[Dict[str, Any]]
    leaves_pool: List[Dict[str, Any]]
    
    # Workflow outputs
    available_workers: List[Dict[str, Any]]
    assigned_schedules: List[Dict[str, Any]]
    shortage_warnings: List[str]
    optimization_summary: str
    errors: List[str]

# 1. Timeline Validation Node
def validate_timeline_node(state: WorkerAgentState) -> Dict[str, Any]:
    errors = []
    try:
        start = datetime.strptime(state["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(state["end_date"], "%Y-%m-%d").date()
        if end <= start:
            errors.append("Schedule end date must be strictly after the start date.")
    except ValueError:
        errors.append("Dates must follow YYYY-MM-DD format.")
    return {"errors": errors}

# 2. Worker Requirements Analysis Node
def analyze_requirements_node(state: WorkerAgentState) -> Dict[str, Any]:
    roles = ["Mason", "Electrician", "Plumber", "Supervisor", "Operator", "Carpenter", "Painter"]
    return {"required_roles": roles}

# 3. Skill Matching Node (Pure)
def skill_matching_node(state: WorkerAgentState) -> Dict[str, Any]:
    # Returns the available workers pool passed in
    return {"available_workers": state.get("workers_pool", [])}

# 4. Shift Scheduling Node (Pure)
def shift_scheduling_node(state: WorkerAgentState) -> Dict[str, Any]:
    schedules = []
    try:
        start_date = datetime.strptime(state["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(state["end_date"], "%Y-%m-%d").date()
        
        leaves_pool = state.get("leaves_pool", [])
        workers_on_leave = set()
        
        for leaf in leaves_pool:
            l_start = datetime.strptime(leaf["start_date"], "%Y-%m-%d").date() if isinstance(leaf["start_date"], str) else leaf["start_date"]
            l_end = datetime.strptime(leaf["end_date"], "%Y-%m-%d").date() if isinstance(leaf["end_date"], str) else leaf["end_date"]
            if leaf["status"] == "Approved" and l_start <= end_date and l_end >= start_date:
                workers_on_leave.add(leaf["worker_id"])
        
        for idx, worker in enumerate(state.get("available_workers", [])):
            if worker["worker_id"] in workers_on_leave:
                continue
                
            shift = "Night" if idx % 3 == 0 else "Day"
            schedules.append({
                "worker_id": worker["worker_id"],
                "worker_name": worker["full_name"],
                "role_title": worker["role_title"],
                "shift_type": shift,
                "start_date": state["start_date"],
                "end_date": state["end_date"]
            })
    except Exception as e:
        logger.error(f"Error compiling shift schedules: {e}")
        
    return {"assigned_schedules": schedules}

# 5. Shortage Prediction Node
def shortage_prediction_node(state: WorkerAgentState) -> Dict[str, Any]:
    warnings = []
    assigned_roles = [s["role_title"] for s in state.get("assigned_schedules", [])]
    
    for role in state.get("required_roles", []):
        count = assigned_roles.count(role)
        if count < 2:
            warnings.append(
                f"Shortage Alert: Role '{role}' has only {count} workers allocated (minimum target: 2)."
            )
    return {"shortage_warnings": warnings}

# 6. AI Shift Optimizer Node (Groq LLM)
def ai_optimization_node(state: WorkerAgentState) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY", "")
    
    prompt = f"""
    You are an expert AI Construction Worker Scheduling Optimizer.
    We have structured the scheduling allocations for a construction project phase:

    Start Date: {state['start_date']}
    End Date: {state['end_date']}
    Allocations total: {len(state.get('assigned_schedules', []))} workers

    Assigned Shift Rosters:
    {json.dumps(state.get('assigned_schedules', []))}

    Predicted Worker Shortage Warnings:
    {json.dumps(state.get('shortage_warnings', []))}

    Optimize the scheduling allocations to minimize overtime costs, match worker skills efficiently, and rotate shifts to reduce fatigue.
    Provide a detailed executive analysis and specific rotation recommendations in Markdown.
    """

    if not api_key:
        logger.warning("GROQ_API_KEY environment variable not found. Using sandbox fallback optimization.")
        summary = (
            f"Allocated {len(state.get('assigned_schedules', []))} workers from {state['start_date']} to {state['end_date']}. "
            "Optimization schedules advise rotating excavator operators every 8 hours and cross-training masons."
        )
        return {"optimization_summary": summary}

    try:
        chat = ChatGroq(
            temperature=0.2,
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile"
        )
        msg = chat.invoke([HumanMessage(content=prompt)])
        return {"optimization_summary": msg.content}
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return {"optimization_summary": "Shift plan roster optimized. AI overtime optimization failed due to API limits."}

# 7. Finalizer Node
def finalize_worker_schedule_node(state: WorkerAgentState) -> Dict[str, Any]:
    return {"project_id": state["project_id"]}

# Define State Machine
workflow = StateGraph(WorkerAgentState)

workflow.add_node("validate_timeline", validate_timeline_node)
workflow.add_node("analyze_requirements", analyze_requirements_node)
workflow.add_node("match_skills", skill_matching_node)
workflow.add_node("allocate_shifts", shift_scheduling_node)
workflow.add_node("predict_shortages", shortage_prediction_node)
workflow.add_node("optimize_shifts", ai_optimization_node)
workflow.add_node("finalize_schedule", finalize_worker_schedule_node)

workflow.set_entry_point("validate_timeline")

def route_after_validation(state: WorkerAgentState):
    if state.get("errors"):
        return "finalize_schedule"
    return "analyze_requirements"

workflow.add_conditional_edges(
    "validate_timeline",
    route_after_validation,
    {
        "finalize_schedule": "finalize_schedule",
        "analyze_requirements": "analyze_requirements"
    }
)

workflow.add_edge("analyze_requirements", "match_skills")
workflow.add_edge("match_skills", "allocate_shifts")
workflow.add_edge("allocate_shifts", "predict_shortages")
workflow.add_edge("predict_shortages", "optimize_shifts")
workflow.add_edge("optimize_shifts", "finalize_schedule")
workflow.add_edge("finalize_schedule", END)

worker_scheduler_agent = workflow.compile()
