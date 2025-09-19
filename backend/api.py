import logging
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.chains.sql_rag_chain import get_sql_rag_chain

# Configuração do App FastAPI
app = FastAPI(
    title="SuppBot RAG API",
    description="API para interagir com o chatbot de logística",
    version="1.0.0"
)

# Configuração do CORS
# Permite que o frontend (rodando em http://localhost:3000) se comunique com o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carrega a cadeia RAG na inicialização
rag_chain = get_sql_rag_chain()

# Modelos de dados para a requisição e resposta
class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Recebe uma pergunta, processa na cadeia RAG e retorna a resposta do LLM.
    """
    try:
        llm_output_str = rag_chain.invoke({"question": request.question})
        
        # A saída do LLM é uma string. Precisamos tentar convertê-la para JSON.
        try:
            # Tenta analisar a string como JSON
            response_json = json.loads(llm_output_str)
            return response_json
        except json.JSONDecodeError:
            # Se falhar, o LLM não gerou um JSON válido.
            # Empacotamos como uma resposta de texto para manter a consistência.
            logging.warning("LLM output was not valid JSON. Returning as text.")
            return {"type": "text", "content": llm_output_str}

    except Exception as e:
        logging.error(f"Erro no processamento da cadeia RAG: {e}", exc_info=True)
        return {"type": "text", "content": "Desculpe, ocorreu um erro ao processar sua solicitação."}

@app.get("/")
def read_root():
    return {"status": "SuppBot API is running"}