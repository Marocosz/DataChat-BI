# =============================================================================
# ARQUIVO DA API WEB (PONTO DE ENTRADA DO SERVIDOR)
#
# Este arquivo utiliza o framework FastAPI para criar um servidor web.
# Ele atua como a interface entre o nosso frontend (React) e a lógica
# complexa das cadeias de IA (LangChain).
#
# Responsabilidades:
# 1. Iniciar e configurar o servidor web.
# 2. Definir os "endpoints" (as URLs que o frontend pode chamar).
# 3. Lidar com requisições HTTP, validando os dados recebidos.
# 4. Orquestrar a chamada para a cadeia de IA principal.
# 5. Retornar as respostas formatadas em JSON para o frontend.
# =============================================================================

# --- Bloco de Importações ---
import logging
import json
import time
from fastapi import FastAPI
# Importa o middleware de CORS para permitir a comunicação entre nosso backend e frontend.
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# Importa a função "maestro" que constrói nossa cadeia de IA completa.
from app.chains.sql_rag_chain import create_master_chain
from app.api import dashboard

# --- Configuração do Logging ---
# Este bloco configura o sistema de logging para toda a aplicação.
# Por estar no arquivo de entrada, garante que todos os módulos que forem importados
# depois dele usarão esta mesma configuração.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Instanciação da Aplicação FastAPI ---
app = FastAPI(
    title="SuppBot RAG API",
    description="API para interagir com o chatbot de logística",
    version="1.0.0"
)

# --- Configuração do CORS (Cross-Origin Resource Sharing) ---
# Essencial para o desenvolvimento local, onde o frontend (em localhost:3000)
# e o backend (em localhost:8000) estão em "origens" diferentes.
# Este middleware adiciona cabeçalhos à resposta do servidor que dizem ao navegador:
# "É seguro permitir que o código de localhost:3000 acesse os recursos deste servidor."
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Lista de origens permitidas.
    allow_credentials=True, # Permite o envio de cookies.
    allow_methods=["*"],    # Permite todos os métodos HTTP (GET, POST, etc.).
    allow_headers=["*"],    # Permite todos os cabeçalhos HTTP.
)

# Inclui as rotas definidas em dashboard.py na aplicação principal,
# com o prefixo /api/dashboard.
app.include_router(dashboard.router, prefix="/api/dashboard")

# --- Carregamento da Cadeia de IA na Inicialização ---
# Chamamos a função create_master_chain() UMA VEZ, quando o servidor inicia.
# O objeto complexo da cadeia é montado e armazenado na variável 'rag_chain'.
# Isso é muito eficiente, pois reutilizamos o mesmo objeto para todas as requisições,
# em vez de reconstruí-lo a cada pergunta do usuário.
rag_chain = create_master_chain()

# --- Definição dos Modelos de Dados ---
# Usando Pydantic, definimos a "forma" que o JSON da requisição deve ter.
class ChatRequest(BaseModel):
    # A requisição deve ter uma chave "question" cujo valor é uma string.
    question: str


# --- Definição dos Endpoints da API ---

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Recebe uma pergunta do frontend, processa na cadeia principal e retorna a resposta.
    """
    start_time = time.monotonic() # Marca o tempo de início
    try:
        # A cadeia agora sempre retorna um dicionário, seja de um gráfico ou de texto.
        # Aqui, invocamos a cadeia pré-carregada com a pergunta do usuário.
        response_dict = rag_chain.invoke({"question": request.question})
        
        end_time = time.monotonic() # Marca o tempo de fim
        duration = end_time - start_time
        
        # Adiciona a nova informação ao dicionário que será enviado ao frontend
        response_dict['response_time'] = f"{duration:.2f}" 
        
        # FastAPI converte automaticamente o dicionário Python em uma resposta JSON para o frontend.
        return response_dict
    
    except Exception as e:

        logging.error(f"Erro no processamento da cadeia RAG: {e}", exc_info=True)
        return {"type": "text", "content": "Desculpe, ocorreu um erro grave ao processar sua solicitação."}


@app.get("/")
def read_root():
    """Endpoint 'health check' para verificar se a API está no ar."""
    return {"status": "SuppBot API is running"}