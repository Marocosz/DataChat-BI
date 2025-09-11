from pydantic import BaseModel, Field

# Modelo para o corpo da requisição (o que o usuário envia)
class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Pergunta do usuário para o chatbot."
    )

# Modelo para o corpo da resposta (o que a API retorna)
class ChatResponse(BaseModel):
    answer: str = Field(
        ...,
        description="Resposta gerada pelo chatbot."
    )