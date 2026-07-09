import os
import json
import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class VoiceAgentState(TypedDict):
    user_id: int
    project_id: Optional[int]
    command_text: str
    intent: str
    project_data: Optional[Dict[str, Any]]
    response_text: str
    errors: List[str]

api_key = os.getenv("GROQ_API_KEY", "")

def parse_intent_node(state: VoiceAgentState) -> Dict[str, Any]:
    """
    Parses the command_text to identify the user's operational query intent.
    Supported intents: get_budget, get_progress, get_workers, get_safety_issues, get_risks, unknown
    """
    text = state.get("command_text", "").lower()
    intent = "unknown"
    
    if api_key:
        prompt = f"""
        You are a construction voice command parsing module.
        Analyze the spoken text query and return the single key mapping to the intent.
        
        Spoken query: "{state.get('command_text')}"
        
        Intent Mapping Rules:
        - "get_budget": query is about project cost, budget, pricing, or financial allocations.
        - "get_progress": query is about project progress, status, milestone completion dates, or schedule timelines.
        - "get_workers": query is about workers, shift schedules, labor attendance, or trade skills.
        - "get_safety_issues": query is about site images safety, visual hazards, PPE issues, or site inspections.
        - "get_risks": query is about delay predictions, risk index scores, or weather threats.
        - "unknown": if the query does not match any of these.
        
        Return ONLY a JSON block in this exact format:
        {{"intent": "intent_key"}}
        """
        try:
            chat = ChatGroq(
                temperature=0.1,
                groq_api_key=api_key,
                model_name="llama-3.3-70b-versatile"
            )
            msg = chat.invoke([HumanMessage(content=prompt)])
            # Clean JSON formatting from model output
            clean_content = msg.content.strip()
            if "{" in clean_content and "}" in clean_content:
                clean_content = clean_content[clean_content.find("{"):clean_content.rfind("}")+1]
            data = json.loads(clean_content)
            intent = data.get("intent", "unknown")
        except Exception as e:
            logger.error(f"Error in LLM intent parsing: {e}. Falling back to keywords.")
            
    if intent == "unknown":
        # Fallback keyword matching
        if any(w in text for w in ["budget", "cost", "money", "expenditure", "price"]):
            intent = "get_budget"
        elif any(w in text for w in ["progress", "completion", "status", "stage", "timeline"]):
            intent = "get_progress"
        elif any(w in text for w in ["worker", "attendance", "labor", "schedule", "people"]):
            intent = "get_workers"
        elif any(w in text for w in ["safety", "hazard", "gear", "ppe", "image", "photo"]):
            intent = "get_safety_issues"
        elif any(w in text for w in ["risk", "delay", "threat", "weather"]):
            intent = "get_risks"
            
    return {"intent": intent}

def generate_voice_response_node(state: VoiceAgentState) -> Dict[str, Any]:
    """
    Synthesizes a response narrative designed for text-to-speech reading.
    Incorporates project_data aggregates retrieved by service layer based on intent.
    """
    intent = state.get("intent", "unknown")
    project_data = state.get("project_data") or {}
    project_name = project_data.get("project_name", "the project")
    
    if not project_data:
        response_text = f"I could not retrieve data for project ID {state.get('project_id')}. Please check project member settings."
        return {"response_text": response_text}
        
    if not api_key:
        logger.info("GROQ_API_KEY not found. Using local template engine for voice response.")
        if intent == "get_budget":
            response_text = (
                f"Here is the budget summary for {project_name}. The estimated total budget is "
                f"INR {project_data.get('estimated_cost', 0.0):,.2f}, and optimized budget is "
                f"INR {project_data.get('optimized_cost', 0.0):,.2f}."
            )
        elif intent == "get_progress":
            response_text = (
                f"For {project_name}, overall project completion is currently at "
                f"{project_data.get('overall_completion', 0.0)}%. The schedule variance shows a delay of "
                f"{project_data.get('variance_days', 0)} days."
            )
        elif intent == "get_workers":
            response_text = (
                f"Regarding the workforce of {project_name}, there are {project_data.get('active_workers_count', 0)} "
                f"workers allocated on active shifts today."
            )
        elif intent == "get_safety_issues":
            issues = project_data.get("safety_issues", [])
            issues_str = " ".join(issues) if issues else "No active hazards reported."
            response_text = (
                f"The latest visual site inspection reports for {project_name} identify the following issues: "
                f"{issues_str}"
            )
        elif intent == "get_risks":
            response_text = (
                f"The predictive risk index score for {project_name} is currently "
                f"{project_data.get('risk_score', 0)} out of 100. Delay probability is at "
                f"{project_data.get('delay_probability', 0.0)}%."
            )
        else:
            response_text = f"Hello. I parsed your query, but could not identify a valid construction operations intent. Try asking about budget, progress, workers, safety, or risks."
        return {"response_text": response_text}
        
    prompt = f"""
    You are the voice assistant for APEXBuild, an AI Construction control system.
    Generate a spoken-style response that will be read aloud to the user.
    Keep the answer conversational, professional, concise, and focused on the data points.
    
    Intent Category: {intent}
    Query details: "{state.get('command_text')}"
    Project Name: {project_name}
    Project Data Context:
    {json.dumps(project_data)}
    
    Return a paragraph of spoken feedback. Speak figures (like INR amounts, percents, day counts) clearly. Avoid any Markdown formatting or emojis in your final output, as it is going to be translated directly to voice.
    """
    
    try:
        chat = ChatGroq(
            temperature=0.3,
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile"
        )
        msg = chat.invoke([HumanMessage(content=prompt)])
        return {"response_text": msg.content.strip()}
    except Exception as e:
        logger.error(f"Error calling Groq for voice response synthesis: {e}")
        return {"response_text": f"Here is the data for {project_name}. Please check the dashboard panels."}

# Build LangGraph
workflow = StateGraph(VoiceAgentState)
workflow.add_node("parse_intent", parse_intent_node)
workflow.add_node("generate_response", generate_voice_response_node)

workflow.set_entry_point("parse_intent")
workflow.add_edge("parse_intent", "generate_response")
workflow.add_edge("generate_response", END)

voice_command_agent = workflow.compile()
