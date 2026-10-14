import ast
import json
import re
import uuid
from typing import Literal
import joblib
from fastapi import FastAPI , HTTPException
import pandas as pd
from pydantic import BaseModel , Field
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from tools import lookup_aurora_heights_knowledge, calculate_aurora_heights_price






# ------------------------------------------------------------------
# 1. Define Tools (Agent Capabilities)
# ------------------------------------------------------------------
tools = [lookup_aurora_heights_knowledge, calculate_aurora_heights_price]
TOOL_NAMES = {t.name for t in tools}

# ------------------------------------------------------------------
# 2. Bind Tools to LLM
# ------------------------------------------------------------------
llm = ChatOllama(
   model="llama3.1:8b",
     temperature=0.1
    # reasoning=False,          # uncomment to turn off thinking (needs recent langchain-ollama)
).bind_tools(tools)

SYSTEM_PROMPT = SystemMessage(content=(
    "You are a real-estate assistant for Aurora Heights. "
    "Use the provided tools to answer pricing and project questions. "
    "Currency: PKR"
    "When you need a tool, call it through the tool-calling interface. "
    "Also get the Document name from which they are giving you the answer and attach at the end of response. "
    "Never print tool names or JSON arguments as text in your reply. "
    "After receiving a tool result, answer the user in plain language. "
    "If required details for a price calculation are missing, ask the user "
    "for them instead of guessing."
))

# ------------------------------------------------------------------
# 3. Safety net: catch tool calls the model wrote as plain text
# ------------------------------------------------------------------
def extract_tool_call(text: str):
    """Detect tool-call JSON written as text (handles True/False and code fences)."""
    if not text:
        return None
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    if not text.startswith("{"):
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            data = ast.literal_eval(text)   # handles Python-style True/False/None
        except Exception:
            return None
    if not isinstance(data, dict) or data.get("name") not in TOOL_NAMES:
        return None
    return {
        "name": data["name"],
        "args": data.get("parameters") or data.get("arguments") or {},
        "id": str(uuid.uuid4()),
        "type": "tool_call",
    }

# ------------------------------------------------------------------
# 4. Agentic Workflow (ReAct / Tool-Calling Loop)
# ------------------------------------------------------------------
def agent_node(state: MessagesState):
    """Core decision-making node. Returns a response or a tool call request."""
    messages = [SYSTEM_PROMPT] + state["messages"]   # system prompt added on every call
    response = llm.invoke(messages)

    # If the model leaked a tool call as plain text, convert it to a real one
    if not response.tool_calls:
        tc = extract_tool_call(response.content)
        if tc:
            response = AIMessage(content="", tool_calls=[tc])

    return {"messages": [response]}

def should_continue(state: MessagesState) -> Literal["tools"]:
    """Router: go to tools if the model requested one, otherwise finish."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

# Graph construction
workflow = StateGraph(MessagesState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# ------------------------------------------------------------------
# 5. FastAPI Setup
# ------------------------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ChatRequest(BaseModel):
    thread_id: str
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    final_state = await graph.ainvoke(
        {"messages": [("user", request.message)]},
        config=config,
    )

    last_message = final_state["messages"][-1]

    return {
        "thread_id": request.thread_id,
        "response": last_message.content,
        "history_length": len(final_state["messages"]),
    }



try:
    model_pipeline = joblib.load("notebook\\lead_scoring_model.joblib")
except Exception as e:
    model_pipeline = None


# 2. Define Request Schema
class LeadRequest(BaseModel):
    source_clean: str = Field(..., example="facebook")
    city_clean: str = Field(..., example="Abbottabad")


# 3. Define Response Schema
class LeadResponse(BaseModel):
    conversion_probability: float
    conversion_percentage: str
    priority_level: str


# 4. POST Endpoint for Scoring
@app.post("/predict_lead", response_model=LeadResponse)
def predict_lead(lead: LeadRequest):
    if model_pipeline is None:
        raise HTTPException(
            status_code=500,
            detail="Model file 'lead_scoring_model.joblib' not loaded. Ensure file exists in working directory.",
        )

    # Convert incoming request to a single-row Pandas DataFrame matching model features
    input_data = pd.DataFrame(
        [{"source_clean": lead.source_clean, "city_clean": lead.city_clean}]
    )

    # Predict conversion probability
    prob = float(model_pipeline.predict_proba(input_data)[0][1])

    # Assign a priority tag for sales reps
    if prob >= 0.50:
        priority = "High"
    elif prob >= 0.20:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "conversion_probability": round(prob, 4),
        "conversion_percentage": f"{prob:.1%}",
        "priority_level": priority,
    }