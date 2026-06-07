"""Chat API router for AI agents."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.chatbots import AGENTS, route_query, auto_route

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    agent: Optional[str] = None


class ChatResponse(BaseModel):
    agent: str
    query: str
    answer: str
    citations: list


@router.get("/agents")
def list_agents():
    return {
        "agents": [
            {
                "key": key,
                "name": bot.name,
                "icon": bot.icon,
                "description": bot.description,
            }
            for key, bot in AGENTS.items()
        ]
    }


@router.post("/query", response_model=ChatResponse)
def chat_query(payload: ChatRequest):
    if not payload.query.strip():
        raise HTTPException(400, "Query cannot be empty")
    if len(payload.query) > 1000:
        raise HTTPException(400, "Query too long (max 1000 chars)")
    if payload.agent:
        return route_query(payload.agent, payload.query)
    return auto_route(payload.query)


@router.get("/query")
def chat_query_get(q: str, agent: Optional[str] = None):
    if not q.strip():
        raise HTTPException(400, "Query cannot be empty")
    if agent:
        return route_query(agent, q)
    return auto_route(q)
