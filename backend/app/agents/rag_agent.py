import os
import logging
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

# State definition
class DrawingRAGState(TypedDict):
    query: str
    context: str
    answer: str
    recommendations: List[str]

# Environment key
api_key = os.getenv("GROQ_API_KEY")

def answer_query_node(state: DrawingRAGState) -> Dict[str, Any]:
    """Generates precise answer based on retrieved drawing chunks."""
    query = state["query"]
    context = state["context"]
    
    if not context:
        return {"answer": "No relevant drawing documents found in the database. Please upload drawings first."}

    if not api_key:
        logger.warning("GROQ_API_KEY environment variable not found. Using sandbox fallback drawing Q&A.")
        # Rule-based heuristics for testing
        q_lower = query.lower()
        if "concrete" in q_lower:
            ans = "The specs declare concrete grade M25 with standard water-cement ratio of 0.45. Volume required is estimated at 450 cu.m."
        elif "foundation" in q_lower or "depth" in q_lower:
            ans = "Foundation depth must be minimum 2.5 meters below ground level as specified in section 4.2."
        elif "plumbing" in q_lower:
            ans = "Plumbing layout utilizes CPVC pipes for internal distribution and UPVC pipes for drainage lines."
        elif "electrical" in q_lower:
            ans = "Electrical lines specify FRLS PVC conduits with copper conductors conforming to IS:694."
        else:
            ans = f"Based on the drawing context, the specification details are: {context[:200]}..."
        return {"answer": ans}

    # Groq compilation
    prompt = (
        "You are an AI Construction Drawing Assistant. Read the following extracted drawing context and answer the query.\n"
        "Reference page numbers or section codes where available in the context.\n\n"
        f"Drawing Context:\n{context}\n\n"
        f"Query: {query}\n\n"
        "Provide a direct, engineering-grade answer. Do not summarize unless asked."
    )
    
    try:
        chat = ChatGroq(temperature=0.1, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
        msg = chat.invoke([HumanMessage(content=prompt)])
        return {"answer": msg.content.strip()}
    except Exception as e:
        logger.error(f"Groq drawing Q&A call failed: {e}")
        return {"answer": "LLM query error. Please check your API key quota."}

def safety_recommendations_node(state: DrawingRAGState) -> Dict[str, Any]:
    """Appends safety best practices and engineering recommendations."""
    query = state["query"]
    context = state["context"]
    
    if not api_key:
        # Static engineering safety standards
        recs = [
            "Ensure excavation walls are sloped or shored to prevent soil collapse.",
            "Test concrete cubes at 7 and 28 days for compressive strength compliance.",
            "Verify all plumbing junctions are pressure-tested before concealing.",
            "Use flame-retardant low-smoke (FRLS) wiring exclusively."
        ]
        return {"recommendations": recs}

    prompt = (
        "You are an AI Construction Safety Inspector. Review the drawing query and context, and suggest a list of 3-4 safety and compliance recommendations.\n\n"
        f"Query: {query}\n"
        f"Drawing Context:\n{context}\n\n"
        "Format as a list of bullet points. Start each item with a brief header."
    )

    try:
        chat = ChatGroq(temperature=0.2, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
        msg = chat.invoke([HumanMessage(content=prompt)])
        
        # Parse recommendations into a list of strings
        raw_recs = msg.content.strip().split("\n")
        parsed = [r.replace("-", "").replace("*", "").strip() for r in raw_recs if r.strip()]
        return {"recommendations": parsed[:5]}
    except Exception as e:
        logger.error(f"Groq recommendations call failed: {e}")
        return {"recommendations": ["Follow standard OSHA compliance guidelines."]}

# Define LangGraph StateGraph
workflow = StateGraph(DrawingRAGState)

workflow.add_node("answer_query", answer_query_node)
workflow.add_node("safety_recommendations", safety_recommendations_node)

workflow.set_entry_point("answer_query")
workflow.add_edge("answer_query", "safety_recommendations")
workflow.add_edge("safety_recommendations", END)

rag_prediction_agent = workflow.compile()
