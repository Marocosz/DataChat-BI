# backend/app/api/endpoints/chat.py

from fastapi import APIRouter, Depends, HTTPException
from app.api.models.chat_models import ChatRequest, ChatResponse
from app.api.services.chatbot_service import ChatbotService, chatbot_service
import uuid

router = APIRouter()

def get_chatbot_service() -> ChatbotService:
    return chatbot_service

@router.post("/query", response_model=ChatResponse, summary="Processa uma pergunta para o chatbot")
async def handle_chat_query(
    request: ChatRequest,
    service: ChatbotService = Depends(get_chatbot_service)
):
    if not request.query:
        raise HTTPException(status_code=400, detail="A query não pode estar vazia.")
    
    # Se nenhum session_id for enviado, cria um novo.
    session_id = request.session_id or str(uuid.uuid4())
    
    response_text = service.get_response(request.query, session_id)
    
    # Retorna a resposta e o session_id para o frontend
    return ChatResponse(answer=response_text, session_id=session_id)