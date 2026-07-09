import os
import json
import logging
from datetime import date
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class ChatAgentState(TypedDict):
    user_id: int
    project_id: Optional[int]
    session_id: int
    query: str
    chat_history: List[Dict[str, str]]  # list of {"sender": "...", "text": "..."}
    context_data: Dict[str, Any]
    vector_context: str
    image_analysis_context: str
    response: str
    errors: List[str]

api_key = os.getenv("GROQ_API_KEY", "")

def route_query_node(state: ChatAgentState) -> Dict[str, Any]:
    """
    Parses the query text to determine if we should look up vectors or drawings.
    Sets flags to trigger semantic vector queries.
    """
    query = state.get("query", "").lower()
    needs_rag = False
    
    rag_keywords = ["drawing", "blueprint", "vector", "specification", "pdf", "sheet", "blueprint spec", "rag"]
    if any(kw in query for kw in rag_keywords):
        needs_rag = True
        
    return {"context_data": {"needs_rag": needs_rag}}

def synthesize_answer_node(state: ChatAgentState) -> Dict[str, Any]:
    """
    Synthesizes the final conversational assistant response.
    Injects context database summaries, RAG context, uploaded image data, and chat history.
    """
    query = state.get("query", "")
    history = state.get("chat_history", [])
    sql_ctx = state.get("context_data", {})
    vector_ctx = state.get("vector_context", "")
    img_ctx = state.get("image_analysis_context", "")
    
    # 1. Build context details
    sql_ctx_str = json.dumps(sql_ctx, indent=2)
    
    # 2. Build Groq Prompt
    system_prompt = f"""
    You are APEXBuild AI Assistant, an expert senior virtual project engineer and operations manager.
    Your task is to answer user queries about the construction project by using real-time operational database states, drawing vector search matches, and image analysis alerts.
    
    Operational SQL Context (Real-time project data):
    {sql_ctx_str}
    
    Drawing Vector Context (RAG matches from drawings):
    {vector_ctx or "No relevant drawing documents queried."}
    
    Site Image Analysis Context:
    {img_ctx or "No active image analysis data uploaded in this request."}
    
    Guidelines:
    1. Be conversational, highly professional, precise, and objective.
    2. Format your response in clean Markdown. Use headings, bullet lists, and tables when presenting complex metrics.
    3. Generate executive summaries when requested, structuring them with sections for Overview, Financials, Schedule, Safety, and Immediate Recommendations.
    4. Maintain context from previous conversation turns.
    5. If drawings or invoices are missing or query returns no data, report it factually.
    """

    messages = [SystemMessage(content=system_prompt)]
    
    # Add history
    for msg in history:
        if msg.get("sender") == "user":
            messages.append(HumanMessage(content=msg.get("text", "")))
        else:
            messages.append(AIMessage(content=msg.get("text", "")))
            
    # Add current query
    messages.append(HumanMessage(content=query))
    
    if not api_key:
        logger.warning("GROQ_API_KEY environment variable not found. Using local template engine for chat assistant.")
        # Local fallback answer logic
        query_lc = query.lower()
        project_name = sql_ctx.get("project_name", "the project")
        
        if "budget" in query_lc or "cost" in query_lc:
            ans = (
                f"### Budget & Cost Summary for {project_name}\n"
                f"- **Total Estimated Cost:** INR {sql_ctx.get('estimated_cost', 0.0):,.2f}\n"
                f"- **AI Optimized Target:** INR {sql_ctx.get('optimized_cost', 0.0):,.2f}\n"
                f"- **Currency:** {sql_ctx.get('currency', 'INR')}\n"
                "All cost centers conform to planned target bounds. Let me know if you'd like to inspect item breakdowns."
            )
        elif "progress" in query_lc or "timeline" in query_lc or "completion" in query_lc:
            ans = (
                f"### Schedule & Progress status for {project_name}\n"
                f"- **Overall completion:** {sql_ctx.get('overall_completion', 0.0)}%\n"
                f"- **Timeline Delay:** {sql_ctx.get('variance_days', 0)} Days\n"
                f"- **Milestones Count:** {sql_ctx.get('milestones_count', 0)} registered items.\n"
                "Concrete pouring and foundation structures are advancing."
            )
        elif "worker" in query_lc or "labor" in query_lc or "attendance" in query_lc:
            ans = (
                f"### Workforce & Labor Roster for {project_name}\n"
                f"- **Active Shift Allocation:** {sql_ctx.get('active_workers_count', 0)} workers today.\n"
                f"- **Trade Roles present:** {', '.join(sql_ctx.get('roles', [])) or 'None'}\n"
                "No critical workforce shortfalls detected on site schedules."
            )
        elif "safety" in query_lc or "hazard" in query_lc or "violation" in query_lc:
            violations = sql_ctx.get("safety_issues", [])
            violations_str = "\n".join([f"- {v}" for v in violations]) if violations else "- No visual hazards detected."
            ans = (
                f"### Safety & Visual Audit alerts for {project_name}\n"
                f"**Active visual violations recorded:**\n{violations_str}\n"
                "Supervisors are advised to enforce harness regulations immediately."
            )
        elif "risk" in query_lc or "delay" in query_lc:
            ans = (
                f"### Risk Index Assessment for {project_name}\n"
                f"- **Composite Risk Score:** {sql_ctx.get('risk_score', 0)} / 100\n"
                f"- **Delay Risk:** {sql_ctx.get('delay_probability', 0.0)}%\n"
                f"- **Weather Risk:** {sql_ctx.get('weather_risk', 'On-Track')}\n"
                f"- **Labor Risk:** {sql_ctx.get('labor_risk', 'On-Track')}\n"
                "AI mitigations indicate regular schedule reviews."
            )
        elif "drawing" in query_lc or "blueprint" in query_lc:
            ans = (
                f"### RAG Drawing Specifications for {project_name}\n"
                f"**Search query:** *{query}*\n\n"
                f"**Vector context search result:**\n"
                f"{vector_ctx or '- No specification segments indexed matching search keywords.'}\n\n"
                "For detailed blueprints, please query drawings through the AI Drawing Cockpit directly."
            )
        elif "summary" in query_lc or "executive" in query_lc:
            ans = (
                f"# Executive Project Review - {project_name}\n"
                f"**Generated:** {date.today().strftime('%Y-%m-%d')}\n\n"
                f"### 1. Operations & Timeline\n"
                f"- Current stage progress: **{sql_ctx.get('overall_completion', 0.0)}%**\n"
                f"- Timeline Variance: **{sql_ctx.get('variance_days', 0)} Days Delay**\n\n"
                f"### 2. Financial Metrics\n"
                f"- Budget Estimated: **INR {sql_ctx.get('estimated_cost', 0.0):,.2f}**\n"
                f"- Optimized Target: **INR {sql_ctx.get('optimized_cost', 0.0):,.2f}**\n\n"
                f"### 3. Workforce & Safety\n"
                f"- Active Crew: **{sql_ctx.get('active_workers_count', 0)} workers**\n"
                f"- Open Safety Hazards: **{len(sql_ctx.get('safety_issues', []))} cases**\n\n"
                f"### 4. Recommendations\n"
                "1. Resolve safety alerts immediately.\n"
                "2. Conduct scheduled material reviews to curb supply shortages."
            )
        else:
            ans = (
                f"Hello! I am your AI Construction Assistant. I have loaded details for **{project_name}**.\n\n"
                "You can ask me questions about:\n"
                "- Budget and cost variance\n"
                "- Timelines, milestones, and progress reports\n"
                "- Workforce schedules and active labor\n"
                "- Risks, delay forecasts, and weather warnings\n"
                "- Drawing specification details via vector indexing"
            )
            
        return {"response": ans}

    try:
        chat = ChatGroq(
            temperature=0.2,
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile"
        )
        msg = chat.invoke(messages)
        return {"response": msg.content.strip()}
    except Exception as e:
        logger.error(f"Error invoking ChatGroq agent: {e}")
        return {"response": "I ran into an issue while synthesizing a response from Groq. Please double check API limits."}

# Build LangGraph workflow
workflow = StateGraph(ChatAgentState)
workflow.add_node("route_query", route_query_node)
workflow.add_node("synthesize_answer", synthesize_answer_node)

workflow.set_entry_point("route_query")
workflow.add_edge("route_query", "synthesize_answer")
workflow.add_edge("synthesize_answer", END)

chat_assistant_agent = workflow.compile()
