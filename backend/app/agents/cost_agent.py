import os
import json
import logging
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class CostAgentState(TypedDict):
    project_id: int
    area_sqft: float
    materials_input: List[Dict[str, Any]]
    labor_input: List[Dict[str, Any]]
    equipment_input: List[Dict[str, Any]]
    currency: str
    
    # Calculated values
    material_cost: float
    labor_cost: float
    equipment_cost: float
    indirect_cost: float
    contingency_cost: float
    estimated_cost: float
    optimized_cost: float
    
    # DB models line items
    budget_items: List[Dict[str, Any]]
    
    # AI optimization results
    ai_summary: str
    ai_recommendations: str
    
    # Errors list
    errors: List[str]

# 1. Validation Node
def validate_input_node(state: CostAgentState) -> Dict[str, Any]:
    errors = []
    if float(state.get("area_sqft", 0)) <= 0:
        errors.append("Project area must be greater than zero.")
        
    for idx, mat in enumerate(state.get("materials_input", [])):
        name = mat.get("material", f"Item {idx + 1}")
        if float(mat.get("quantity", 0)) <= 0:
            errors.append(f"Material '{name}': quantity must be greater than zero.")
        if float(mat.get("unit_price", 0)) <= 0:
            errors.append(f"Material '{name}': unit price must be greater than zero.")

    for idx, lab in enumerate(state.get("labor_input", [])):
        w_type = lab.get("worker_type", f"Type {idx + 1}")
        if int(lab.get("worker_count", 0)) <= 0:
            errors.append(f"Labor '{w_type}': worker count must be greater than zero.")
        if float(lab.get("daily_rate", 0)) <= 0:
            errors.append(f"Labor '{w_type}': daily rate must be greater than zero.")
        if int(lab.get("days", 0)) <= 0:
            errors.append(f"Labor '{w_type}': days must be greater than zero.")

    for idx, eq in enumerate(state.get("equipment_input", [])):
        name = eq.get("equipment_name", f"Equipment {idx + 1}")
        if float(eq.get("daily_rate", 0)) <= 0:
            errors.append(f"Equipment '{name}': daily rate must be greater than zero.")
        if int(eq.get("days_used", 0)) <= 0:
            errors.append(f"Equipment '{name}': days used must be greater than zero.")

    return {"errors": errors}

# 2. Material Cost Calculator
def estimate_materials_node(state: CostAgentState) -> Dict[str, Any]:
    items = []
    total = 0.0
    for mat in state.get("materials_input", []):
        qty = float(mat["quantity"])
        price = float(mat["unit_price"])
        item_total = qty * price
        total += item_total
        
        items.append({
            "category": "Material",
            "description": f"Material: {mat['material']}",
            "quantity": qty,
            "unit_price": price,
            "total_price": item_total
        })
    return {
        "material_cost": total,
        "budget_items": items
    }

# 3. Labor Cost Calculator
def estimate_labor_node(state: CostAgentState) -> Dict[str, Any]:
    items = state.get("budget_items", []).copy()
    total = 0.0
    for lab in state.get("labor_input", []):
        count = int(lab["worker_count"])
        rate = float(lab["daily_rate"])
        days = int(lab["days"])
        item_total = float(count * rate * days)
        total += item_total
        
        items.append({
            "category": "Labor",
            "description": f"Labor: {lab['worker_type']} (Count: {count}, Days: {days})",
            "quantity": float(count * days),
            "unit_price": rate,
            "total_price": item_total
        })
    return {
        "labor_cost": total,
        "budget_items": items
    }

# 4. Equipment Cost Calculator
def estimate_equipment_node(state: CostAgentState) -> Dict[str, Any]:
    items = state.get("budget_items", []).copy()
    total = 0.0
    for eq in state.get("equipment_input", []):
        rate = float(eq["daily_rate"])
        days = int(eq["days_used"])
        item_total = float(rate * days)
        total += item_total
        
        items.append({
            "category": "Equipment",
            "description": f"Equipment: {eq['equipment_name']} (Days: {days})",
            "quantity": float(days),
            "unit_price": rate,
            "total_price": item_total
        })
    return {
        "equipment_cost": total,
        "budget_items": items
    }

# 5. Indirect Cost Calculator (10% of Material + Labor + Equipment)
def estimate_indirect_node(state: CostAgentState) -> Dict[str, Any]:
    items = state.get("budget_items", []).copy()
    subtotal = state["material_cost"] + state["labor_cost"] + state["equipment_cost"]
    indirect = subtotal * 0.10
    
    items.append({
        "category": "Indirect",
        "description": "Indirect site operational costs (10% overhead)",
        "quantity": 1.0,
        "unit_price": indirect,
        "total_price": indirect
    })
    return {
        "indirect_cost": indirect,
        "budget_items": items
    }

# 6. Contingency Calculator (5% of Subtotal + Indirect)
def estimate_contingency_node(state: CostAgentState) -> Dict[str, Any]:
    items = state.get("budget_items", []).copy()
    subtotal = state["material_cost"] + state["labor_cost"] + state["equipment_cost"] + state["indirect_cost"]
    contingency = subtotal * 0.05
    
    items.append({
        "category": "Contingency",
        "description": "Emergency contingency buffer (5% allocation)",
        "quantity": 1.0,
        "unit_price": contingency,
        "total_price": contingency
    })
    
    estimated_cost = subtotal + contingency
    return {
        "contingency_cost": contingency,
        "budget_items": items,
        "estimated_cost": estimated_cost
    }

# 7. AI Budget Optimizer Node (Groq LLM)
def optimize_budget_node(state: CostAgentState) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY", "")
    
    # Calculate totals
    mat_cost = state["material_cost"]
    lab_cost = state["labor_cost"]
    eq_cost = state["equipment_cost"]
    ind_cost = state["indirect_cost"]
    cont_cost = state["contingency_cost"]
    est_cost = state["estimated_cost"]
    
    prompt = f"""
    You are an expert AI Construction Project Estimator.
    We have estimated the initial budget of a construction project.

    Project Area: {state['area_sqft']} sqft
    Initial Cost Estimation Breakdown:
    - Materials Cost: {state['currency']} {mat_cost:,.2f}
    - Labor Cost: {state['currency']} {lab_cost:,.2f}
    - Equipment Rental Cost: {state['currency']} {eq_cost:,.2f}
    - Indirect Overhead Cost: {state['currency']} {ind_cost:,.2f}
    - Contingency Cost: {state['currency']} {cont_cost:,.2f}
    - Total Estimated Cost: {state['currency']} {est_cost:,.2f}

    Itemized Material list input: {json.dumps(state['materials_input'])}
    Itemized Labor worker list input: {json.dumps(state['labor_input'])}
    Itemized Equipment list input: {json.dumps(state['equipment_input'])}

    Optimize this budget. Explain estimated costs, suggest cheaper alternatives, highlight expensive lines, and recommend efficiency improvements (labor counts, rental durations).

    You MUST return your output in the following JSON format ONLY:
    {{
       "optimized_cost": <numeric value representing the new optimized total cost. Do not include currency characters, write numbers only. Must be slightly less than or equal to estimated_cost>,
       "summary": "<executive natural language summary explaining the initial estimate>",
       "recommendations": "<bulleted list of specific cost savings and optimizations>"
    }}
    """

    if not api_key:
        # Fallback Mock Optimization (Resilient Sandbox Mode)
        logger.warning("GROQ_API_KEY environment variable not found. Using sandbox fallback optimization.")
        savings = mat_cost * 0.08 + lab_cost * 0.05
        opt_cost = est_cost - savings
        summary = (
            f"The initial construction estimate is calculated at {state['currency']} {est_cost:,.2f} "
            f"for an area of {state['area_sqft']} sqft. Materials represent {mat_cost/est_cost*100:.1f}% "
            "of the budget, which is within standard benchmarks."
        )
        recommendations = (
            "- Material Savings: Consider bulk purchasing cement and structural steel to save up to 8%.\n"
            "- Equipment efficiency: Optimize the excavator rental duration by overlapping tasks.\n"
            "- Labor tracking: Standardize helper schedules to avoid overlapping shifts."
        )
        return {
            "optimized_cost": opt_cost,
            "ai_summary": summary,
            "ai_recommendations": recommendations
        }

    try:
        chat = ChatGroq(
            temperature=0.2,
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile",
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        msg = chat.invoke([HumanMessage(content=prompt)])
        data = json.loads(msg.content)
        
        return {
            "optimized_cost": float(data.get("optimized_cost", est_cost)),
            "ai_summary": data.get("summary", "Budget optimization completed."),
            "ai_recommendations": data.get("recommendations", "No immediate optimization suggestions.")
        }
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}. Falling back to default optimization.")
        # Fail-safe fallback if API error occurs
        savings = mat_cost * 0.05
        return {
            "optimized_cost": est_cost - savings,
            "ai_summary": "Budget estimate constructed. Groq API optimization failed.",
            "ai_recommendations": "Review high cost items manually to identify potential material alternates."
        }

# 8. Report Finalizer Node
def generate_report_node(state: CostAgentState) -> Dict[str, Any]:
    # Pass values through without mutations to conclude execution
    return {"project_id": state["project_id"]}

# Define LangGraph State Machine
workflow = StateGraph(CostAgentState)

# Add Nodes
workflow.add_node("validate_input", validate_input_node)
workflow.add_node("estimate_materials", estimate_materials_node)
workflow.add_node("estimate_labor", estimate_labor_node)
workflow.add_node("estimate_equipment", estimate_equipment_node)
workflow.add_node("estimate_indirect", estimate_indirect_node)
workflow.add_node("estimate_contingency", estimate_contingency_node)
workflow.add_node("optimize_budget", optimize_budget_node)
workflow.add_node("generate_report", generate_report_node)

# Set Entry
workflow.set_entry_point("validate_input")

# Conditional Router after validation
def route_after_validation(state: CostAgentState):
    if state.get("errors"):
        return "generate_report"
    return "estimate_materials"

workflow.add_conditional_edges(
    "validate_input",
    route_after_validation,
    {
        "generate_report": "generate_report",
        "estimate_materials": "estimate_materials"
    }
)

# Connect remaining nodes sequentially
workflow.add_edge("estimate_materials", "estimate_labor")
workflow.add_edge("estimate_labor", "estimate_equipment")
workflow.add_edge("estimate_equipment", "estimate_indirect")
workflow.add_edge("estimate_indirect", "estimate_contingency")
workflow.add_edge("estimate_contingency", "optimize_budget")
workflow.add_edge("optimize_budget", "generate_report")
workflow.add_edge("generate_report", END)

cost_estimation_agent = workflow.compile()
