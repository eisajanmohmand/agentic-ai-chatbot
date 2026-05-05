from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from agents import route_message, run_agent
import pathlib

HTML = pathlib.Path(__file__).parent / "index.html"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list

@app.get("/")
def root():
    return HTMLResponse(content=HTML.read_text())

@app.post("/chat")
def chat(req: ChatRequest):
    agent_type = route_message(req.message)

    emergency_keywords = ["chest pain", "can't breathe", "cannot breathe", "stroke",
                          "unconscious", "severe bleeding", "not breathing", "heart attack"]
    if agent_type != "emergency" and any(kw in req.message.lower() for kw in emergency_keywords):
        agent_type = "emergency"

    history = req.history + [{"role": "user", "content": req.message}]
    response = run_agent(agent_type, history)

    agent_labels = {
        "symptom": "🩺 Symptom Analysis Agent",
        "medication": "💊 Medication Safety Agent",
        "emergency": "🚑 Emergency Decision Agent",
    }

    return {"response": response, "agent": agent_labels[agent_type]}
