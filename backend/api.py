import logging
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.chains.sql_rag_chain import create_master_chain

# --- Bloco Adicionado: Configuração do Logging ---
# Define o formato e o nível mínimo de logs que serão exibidos
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# --------------------------------------------------

# --- O resto do seu código permanece o mesmo ---

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
rag_chain = create_master_chain()

# Modelos de dados para a requisição e resposta
class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Recebe uma pergunta e retorna diretamente o dicionário da cadeia RAG.
    O parser de JSON e a lógica de formatação agora estão dentro da cadeia.
    """
    try:
        # A cadeia agora sempre retorna um dicionário, seja de um gráfico ou de texto.
        response_dict = rag_chain.invoke({"question": request.question})
        return response_dict
    except Exception as e:
        # Esta linha agora irá funcionar e imprimir o erro detalhado no terminal
        logging.error(f"Erro no processamento da cadeia RAG: {e}", exc_info=True)
        return {"type": "text", "content": "Desculpe, ocorreu um erro grave ao processar sua solicitação."}


@app.get("/")
def read_root():
    return {"status": "SuppBot API is running"}