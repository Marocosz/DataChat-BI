# backend/app/api/endpoints/chat.py
import uuid
from fastapi import APIRouter, Depends
from app.api.models.chat_models import ChatRequest, ChatResponse
from app.api.services.chatbot_service import ChatbotService, chatbot_service

router = APIRouter()

def get_chatbot_service() -> ChatbotService:
    return chatbot_service

@router.post("/query", response_model=ChatResponse)
async def handle_chat_query(
    request: ChatRequest,
    service: ChatbotService = Depends(get_chatbot_service)
):
    session_id = request.session_id or str(uuid.uuid4())
    response_text = service.get_response(request.query, session_id)
    return ChatResponse(answer=response_text, session_id=session_id)