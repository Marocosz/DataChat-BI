# backend/app/api/models/chat_models.py

"""
Este módulo define os "contratos de dados" da nossa API usando a biblioteca Pydantic.
Ele especifica a estrutura exata dos dados que entram (Request) e saem (Response)
do nosso endpoint de chat.

Sua função é garantir a validação automática dos dados, a serialização (conversão
de/para JSON) e a geração da documentação interativa da API. Se uma requisição
chegar com uma estrutura errada, o FastAPI a rejeitará automaticamente com um erro claro.
"""

from pydantic import BaseModel, Field
from typing import Optional

# Define a estrutura esperada para o corpo de uma requisição POST.
class ChatRequest(BaseModel):
    # A pergunta do usuário; é um campo de texto obrigatório e não pode ser vazio.
    query: str = Field(..., min_length=1)
    # O ID da sessão para manter o histórico; é opcional.
    session_id: Optional[str] = None

# Define a estrutura da resposta JSON que a API sempre retornará.
class ChatResponse(BaseModel):
    # A resposta gerada pelo bot; é um campo de texto obrigatório.
    answer: str
    # O ID da sessão, retornado para que o cliente possa continuar a conversa.
    session_id: str