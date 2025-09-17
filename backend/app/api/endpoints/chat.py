# backend/app/api/endpoints/chat.py

"""
Este módulo define um "endpoint" da API usando o framework FastAPI. Um endpoint é
essencialmente uma URL específica no seu servidor que sabe como receber requisições
e enviar respostas. Este arquivo é a porta de entrada para a funcionalidade do chatbot.

Sua função é expor a lógica do nosso ChatbotService para o mundo exterior através
de uma interface web (HTTP). Ele recebe a pergunta do usuário (enviada pelo frontend),
gerencia o ID da sessão da conversa, chama o serviço principal para processar a
pergunta e, finalmente, formata e envia a resposta de volta para o cliente.
"""

import uuid
from fastapi import APIRouter, Depends
from app.api.models.chat_models import ChatRequest, ChatResponse
from app.api.services.chatbot_service import ChatbotService, chatbot_service

# Cria uma instância de APIRouter
router = APIRouter()

def get_chatbot_service() -> ChatbotService:
    """
    Função de dependência do FastAPI.
    Sua única responsabilidade é retornar a instância única (singleton) do
    ChatbotService. O sistema de Injeção de Dependência do FastAPI usará
    esta função para "injetar" o serviço no nosso endpoint.
    """
    return chatbot_service


# - response_model=ChatResponse: Declara que a resposta seguirá o modelo
#   definido em ChatResponse, garantindo validação e documentação automática.
@router.post("/query", response_model=ChatResponse)
async def handle_chat_query(
    # O corpo da requisição POST será validado contra o modelo Pydantic ChatRequest.
    request: ChatRequest,
    # Injeção de Dependência: O FastAPI chama get_chatbot_service e o resultado
    # é passado para o parâmetro 'service'. Isso desacopla nosso endpoint da
    # criação do serviço.
    service: ChatbotService = Depends(get_chatbot_service)
):
    """
    Processa a requisição de chat, gerencia a sessão e retorna a resposta do bot.
    """
    # Lógica de gerenciamento de sessão:
    # Se o cliente enviou um 'session_id', nós o usamos.
    # Se não (indicando uma nova conversa), geramos um novo ID universalmente único (UUID).
    session_id = request.session_id or str(uuid.uuid4())

    # Delega o processamento da pergunta para a camada de serviço, passando a
    # pergunta do usuário e o ID da sessão para manter o contexto da conversa.
    response_text = service.get_response(request.query, session_id)

    # Constrói e retorna a resposta final, seguindo o modelo ChatResponse.
    # É crucial retornar o session_id para que o frontend possa usá-lo na próxima requisição.
    return ChatResponse(answer=response_text, session_id=session_id)