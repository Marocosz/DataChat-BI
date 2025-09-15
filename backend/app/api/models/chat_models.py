# backend/app/api/models/chat_models.py
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str