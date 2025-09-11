# backend/app/api/models/chat_models.py

from pydantic import BaseModel, Field
from typing import Optional

# Adicionamos session_id como um campo opcional
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Pergunta do usuário para o chatbot.")
    session_id: Optional[str] = Field(None, description="ID da sessão para manter o histórico da conversa.")

# A resposta agora também retorna o session_id
class ChatResponse(BaseModel):
    answer: str = Field(..., description="Resposta gerada pelo chatbot.")
    session_id: str = Field(..., description="ID da sessão para continuar a conversa.")