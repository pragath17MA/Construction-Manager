import os
import json
import logging
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class MaterialAgentState(TypedDict):
    project_id: int
    area_sqft: float
    floors: int
    building_type: str
    rooms: int
    timeline_months: int
    budget: float
    project_category: str
    
    # Pools passed from service
    inventory_pool: List[Dict[str, Any]]
    suppliers_pool: List[Dict[str, Any]]
    
    # Workflow outputs
    materials_estimated: List[Dict[str, Any]]
    low_stock_warnings: List[str]
    supplier_recommendations: List[Dict[str, Any]]
    optimization_summary: str
    errors: List[str]

# 1. Validation Node
def validate_project_specs_node(state: MaterialAgentState) -> Dict[str, Any]:
    errors = []
    if float(state.get("area_sqft", 0)) <= 0:
        errors.append("Project area must be greater than zero.")
    if int(state.get("floors", 0)) <= 0:
        errors.append("Floor count must be greater than zero.")
    if float(state.get("budget", 0)) <= 0:
        errors.append("Project budget must be greater than zero.")
    return {"errors": errors}

# 2. Material Estimation Node
def estimate_materials_node(state: MaterialAgentState) -> Dict[str, Any]:
    area = float(state["area_sqft"])
    floors = int(state["floors"])
    rooms = int(state.get("rooms", 1))

    raw_estimates = [
        ("Cement", "Cement", area * 0.4 * floors, "Bags", 400.0),
        ("Structural Steel", "Steel", area * 0.005 * floors, "Tons", 60000.0),
        ("Bricks", "Bricks", area * 12.0 * floors, "Pcs", 8.0),
        ("Sand", "Sand", area * 0.02 * floors, "Cu.m", 1500.0),
        ("Aggregate", "Aggregate", area * 0.03 * floors, "Cu.m", 1800.0),
        ("Concrete", "Concrete", area * 0.05 * floors, "Cu.m", 4500.0),
        ("Paint", "Paint", area * 0.1 * floors, "Liters", 250.0),
        ("Wood", "Wood", area * 0.01 * floors, "Cu.ft", 1200.0),
        ("Glass", "Glass", area * 0.05 * floors, "Sq.ft", 150.0),
        ("Tiles", "Tiles", area * 0.8 * floors, "Sq.ft", 80.0),
        ("Electrical Wiring", "Electrical", float(floors * 2), "Units", 50000.0),
        ("Plumbing Pipes", "Plumbing", float(floors * 2), "Units", 40000.0),
        ("Roofing Sheets", "Roofing", area / floors, "Sq.ft", 120.0),
        ("Finishing", "Finishing Materials", float(floors), "Units", 80000.0),
        ("Doors", "Doors", float(floors * 4 + rooms), "Pcs", 6000.0),
        ("Windows", "Windows", float(floors * 5 + rooms * 1.5), "Pcs", 4000.0),
        ("Hardware fitting", "Hardware", float(floors * 3), "Units", 15000.0)
    ]

    materials_list = []
    for name, cat, qty, unit, price in raw_estimates:
        cost = float(qty) * float(price)
        materials_list.append({
            "material_name": name,
            "category": cat,
            "quantity": float(qty),
            "unit": unit,
            "unit_price": float(price),
            "total_cost": cost
        })
        
    return {"materials_estimated": materials_list}

# 3. Inventory Check Node (Pure)
def check_inventory_node(state: MaterialAgentState) -> Dict[str, Any]:
    warnings = []
    inventory_pool = state.get("inventory_pool", [])
    
    for mat in state.get("materials_estimated", []):
        name = mat["material_name"]
        qty_needed = mat["quantity"]
        
        # Match from pool
        inv = next((i for i in inventory_pool if i["material_name"].lower() == name.lower()), None)
        if not inv:
            warnings.append(f"Material '{name}' has no registered inventory stock records.")
            continue
            
        net_avail = float(inv["quantity_available"]) - float(inv["quantity_reserved"])
        if net_avail < qty_needed:
            warnings.append(
                f"Low Stock Alert: '{name}' requires {qty_needed:,.1f} {mat['unit']} "
                f"but only {net_avail:,.1f} is available in stock."
            )
            
    return {"low_stock_warnings": warnings}

# 4. Supplier Recommendation Node (Pure)
def recommend_suppliers_node(state: MaterialAgentState) -> Dict[str, Any]:
    recommendations = []
    suppliers_pool = state.get("suppliers_pool", [])
    
    # Active suppliers only
    active_suppliers = [s for s in suppliers_pool if s.get("active", True)]
    
    for warning in state.get("low_stock_warnings", []):
        if "'" in warning:
            name = warning.split("'")[1]
        else:
            continue
            
        # Match suppliers and sort by rating desc
        matched_sups = sorted(active_suppliers, key=lambda s: float(s["rating"]), reverse=True)[:2]
        for sup in matched_sups:
            mat_spec = next((m for m in state["materials_estimated"] if m["material_name"] == name), None)
            unit_price = mat_spec["unit_price"] if mat_spec else 100.0
            
            recommendations.append({
                "material_name": name,
                "supplier_id": sup["id"],
                "supplier_name": sup["supplier_name"],
                "rating": float(sup["rating"]),
                "unit_price": float(unit_price),
                "availability_status": "Ready to Deliver"
            })
            
    return {"supplier_recommendations": recommendations}

# 5. Procurement Optimizer Node (Groq LLM)
def optimize_procurement_node(state: MaterialAgentState) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY", "")
    total_cost = sum(m["total_cost"] for m in state["materials_estimated"])
    
    prompt = f"""
    You are an expert AI Construction Procurement Planner.
    We have estimated the material requirements for a project:

    Project Category: {state['project_category']}
    Timeline: {state['timeline_months']} months
    Budget Limit: {state['budget']}
    Estimated Material cost total: {total_cost:,.2f}

    Detailed Materials Estimated:
    {json.dumps(state['materials_estimated'])}

    Stock warnings:
    {json.dumps(state['low_stock_warnings'])}

    Supplier recommendations available:
    {json.dumps(state['supplier_recommendations'])}

    Optimize the procurement plan.
    Identify expensive line items, suggest phased procurement schedules, and outline bulk savings strategies.

    Return your output in this format:
    Provide an executive summary followed by a bulleted optimization guide. Write it in clear Markdown.
    """

    if not api_key:
        logger.warning("GROQ_API_KEY environment variable not found. Using sandbox fallback optimization.")
        summary = (
            f"The project '{state['project_category']}' estimated cost is {total_cost:,.2f}. "
            f"There are {len(state['low_stock_warnings'])} material shortage alerts. "
            "Optimization schedules recommend bulk steel delivery in month 1 and phased concrete deliveries."
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
        return {"optimization_summary": "Procurement plan compiled. AI analysis optimization failed due to API limitations."}

# 6. Finalizer Node
def finalize_material_plan_node(state: MaterialAgentState) -> Dict[str, Any]:
    return {"project_id": state["project_id"]}

# Define State Machine
workflow = StateGraph(MaterialAgentState)

workflow.add_node("validate_specs", validate_project_specs_node)
workflow.add_node("estimate_materials", estimate_materials_node)
workflow.add_node("check_inventory", check_inventory_node)
workflow.add_node("recommend_suppliers", recommend_suppliers_node)
workflow.add_node("optimize_procurement", optimize_procurement_node)
workflow.add_node("finalize_plan", finalize_material_plan_node)

workflow.set_entry_point("validate_specs")

def route_after_validation(state: MaterialAgentState):
    if state.get("errors"):
        return "finalize_plan"
    return "estimate_materials"

workflow.add_conditional_edges(
    "validate_specs",
    route_after_validation,
    {
        "finalize_plan": "finalize_plan",
        "estimate_materials": "estimate_materials"
    }
)

workflow.add_edge("estimate_materials", "check_inventory")
workflow.add_edge("check_inventory", "recommend_suppliers")
workflow.add_edge("recommend_suppliers", "optimize_procurement")
workflow.add_edge("optimize_procurement", "finalize_plan")
workflow.add_edge("finalize_plan", END)

material_planner_agent = workflow.compile()
