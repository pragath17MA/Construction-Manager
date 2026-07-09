import os
import logging
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

# State definition
class InvoiceAgentState(TypedDict):
    invoice_id: int
    total_amount: float
    is_duplicate: bool
    items: List[Dict[str, Any]]
    fraud_risk_score: float
    fraud_risk_details: List[str]
    budget_variance_alerts: List[str]
    ai_fraud_recommendations: str

# Environment key
api_key = os.getenv("GROQ_API_KEY")

def audit_pricing_node(state: InvoiceAgentState) -> Dict[str, Any]:
    """Inspects items pricing structure for potential cost inflations."""
    details = []
    base_risk = 0.0
    
    # Static checking
    for item in state["items"]:
        desc = item.get("desc", "").lower()
        total = item.get("total", 0.0)
        
        # Check for suspicious line-item pricing anomalies
        if "cement" in desc and total > 100000.0:
            details.append(f"Suspiciously high cement volume cost: ₹{total:.2f}")
            base_risk += 15.0
        if "steel" in desc and total > 200000.0:
            details.append(f"Bulk steel charge exceeds limit: ₹{total:.2f}")
            base_risk += 20.0

    return {
        "fraud_risk_details": details,
        "fraud_risk_score": base_risk
    }

def audit_fraud_risk_node(state: InvoiceAgentState) -> Dict[str, Any]:
    """Aggregates duplicate billing indicators and pricing anomalies into a final fraud index."""
    score = state["fraud_risk_score"]
    details = list(state["fraud_risk_details"])
    
    if state["is_duplicate"]:
        score = 100.0
        details.append("CRITICAL: Identical invoice number and vendor details already exist (Double Billing Risk).")
    
    if state["budget_variance_alerts"]:
        score += 15.0
        for alert in state["budget_variance_alerts"]:
            details.append(f"Budget Variance Alert: {alert}")

    final_score = min(100.0, score)
    return {
        "fraud_risk_score": final_score,
        "fraud_risk_details": details
    }

def reconciliation_suggestions_node(state: InvoiceAgentState) -> Dict[str, Any]:
    """Generates AI suggestions for managing budget variances or fraud warnings."""
    score = state["fraud_risk_score"]
    details = state["fraud_risk_details"]
    
    if not api_key:
        logger.warning("GROQ_API_KEY environment variable not found. Using sandbox fallback invoice analyzer.")
        if score > 80.0:
            recs = "WARNING: Highly suspicious transaction. (1) Block payment processing immediately. (2) Audit physical supplier shipping manifests. (3) Request vendor verification."
        elif score > 30.0:
            recs = "ALERT: Moderate risk. Verify actual material receipt logs before signing off budget allocations."
        else:
            recs = "✓ Clean invoice record. Proceed with standard processing and budget updates."
        return {"ai_fraud_recommendations": recs}

    prompt = (
        "You are an AI Forensic Auditor for a construction project.\n"
        "Analyze the following invoice audit indicators and write a concise list of reconciliation actions.\n\n"
        f"Invoice ID: {state['invoice_id']}\n"
        f"Total Amount: ₹{state['total_amount']:.2f}\n"
        f"Is Duplicate Alert: {state['is_duplicate']}\n"
        f"Calculated Fraud Risk Score: {score}/100\n"
        f"Audit Warnings:\n" + "\n".join([f"- {d}" for d in details]) + "\n\n"
        "Write 3 clear recommendations for the project manager. Avoid boilerplate intro/outro phrases."
    )

    try:
        chat = ChatGroq(temperature=0.2, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
        msg = chat.invoke([HumanMessage(content=prompt)])
        return {"ai_fraud_recommendations": msg.content.strip()}
    except Exception as e:
        logger.error(f"Groq invoice audit call failed: {e}")
        return {"ai_fraud_recommendations": "Verify invoice item records physically."}

# Define LangGraph StateGraph
workflow = StateGraph(InvoiceAgentState)

workflow.add_node("audit_pricing", audit_pricing_node)
workflow.add_node("audit_fraud_risk", audit_fraud_risk_node)
workflow.add_node("reconciliation_suggestions", reconciliation_suggestions_node)

workflow.set_entry_point("audit_pricing")
workflow.add_edge("audit_pricing", "audit_fraud_risk")
workflow.add_edge("audit_fraud_risk", "reconciliation_suggestions")
workflow.add_edge("reconciliation_suggestions", END)

invoice_prediction_agent = workflow.compile()
