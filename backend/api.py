import logging
import json
import time
import uuid # Para gerar IDs de sessão únicos
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.chains.sql_rag_chain import create_master_chain
from app.api import dashboard

# Configuração do Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

## INÍCIO DA ATUALIZAÇÃO ##
# Adiciona um logger específico para este arquivo, o que é uma boa prática
# para identificar a origem das mensagens de log.
logger = logging.getLogger(__name__)
## FIM DA ATUALIZAÇÃO ##

# Instanciação da Aplicação FastAPI
app = FastAPI(
    title="SuppBot RAG API",
    description="API para interagir com o chatbot de logística",
    version="1.0.0"
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas do dashboard
app.include_router(dashboard.router, prefix="/api/dashboard")

# Carregamento da Cadeia de IA com memória na Inicialização
rag_chain = create_master_chain()

# Modelo de requisição atualizado para incluir o session_id
class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None # Pode ser uma string (para conversas existentes) ou Nulo (para a primeira mensagem)

# Endpoint de chat atualizado para gerenciar a sessão
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Recebe uma pergunta e um session_id, processa na cadeia com memória
    e retorna a resposta junto com o session_id.
    """
    start_time = time.monotonic()
    
    # Bloco de log para exibir a pergunta do usuário no terminal do backend.
    # Os separadores ajudam a destacar a nova pergunta em meio aos outros logs.
    logger.info("=================================================")
    logger.info(f"--- Nova Pergunta Recebida: '{request.question}'")
    logger.info("=================================================")

    # Gera um novo ID de sessão se for a primeira mensagem da conversa
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # A chamada à cadeia agora precisa de uma configuração especial para passar o session_id
        full_chain_output = rag_chain.invoke(
            {"question": request.question},
            config={"configurable": {"session_id": session_id}}
        )
        
        response_dict = full_chain_output.get("api_response", {})
        
        end_time = time.monotonic()
        duration = end_time - start_time
        
        response_dict['response_time'] = f"{duration:.2f}"
        # Devolvemos o session_id para o frontend para que ele possa usá-lo na próxima pergunta
        response_dict['session_id'] = session_id
        
        return response_dict
        
    except Exception as e:
        # Usamos o logger raiz aqui para erros graves, o que está correto.
        logging.error(f"Erro no processamento da cadeia RAG: {e}", exc_info=True)
        return {"type": "text", "content": "Desculpe, ocorreu um erro grave ao processar sua solicitação."}


@app.get("/")
def read_root():
    """Endpoint 'health check' para verificar se a API está no ar."""
    return {"status": "SuppBot API is running"}