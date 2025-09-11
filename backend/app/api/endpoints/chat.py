# app/api/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException
from app.api.models.chat_models import ChatRequest, ChatResponse
from app.api.services.chatbot_service import ChatbotService, chatbot_service

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
    
    response_text = service.get_response(request.query)
    
    return ChatResponse(answer=response_text)