# =================================================================================================
# =================================================================================================
#
#                           PONTO DE ENTRADA DA API (BACKEND)
#
# Visão Geral do Módulo:
#
# Este arquivo é o coração do backend e serve como o ponto de entrada principal para a aplicação
# FastAPI. Suas responsabilidades incluem:
#
# 1. Inicialização da Aplicação: Cria e configura a instância principal do FastAPI.
#
# 2. Configuração de CORS: Define as regras de Cross-Origin Resource Sharing, permitindo
#    que o frontend (rodando em http://localhost:3000) se comunique com este backend.
#
# 3. Carregamento do Modelo de IA: Invoca a função `create_master_chain()` do módulo de RAG
#    para carregar a cadeia de IA com memória uma única vez durante a inicialização do servidor.
#    Isso é uma otimização crucial de performance.
#
# 4. Definição de Endpoints (Rotas):
#    - `/chat` (POST): O endpoint principal que recebe as perguntas do usuário, gerencia os
#      IDs de sessão e retorna as respostas geradas pela cadeia de IA.
#    - `/` (GET): Um endpoint de "health check" para verificar se a API está no ar.
#    - `/api/dashboard`: Registra todas as rotas relacionadas ao dashboard.
#
# 5. Gerenciamento de Sessão: Implementa a lógica para criar um novo ID de sessão para
#    novas conversas ou reutilizar um ID existente para conversas contínuas.
#
# =================================================================================================
# =================================================================================================

import logging
import json
import time
import uuid  # Importa a biblioteca para gerar IDs de sessão únicos.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel # Usado para definir os modelos de dados das requisições.

# Importa a função que constrói a cadeia de IA principal.
from app.chains.sql_rag_chain import create_master_chain
# Importa o roteador que contém os endpoints do dashboard.
from app.api import dashboard

# Configura o sistema de logging para toda a aplicação.
# Define o nível mínimo de log a ser exibido (INFO) e o formato das mensagens.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Cria um logger específico para este arquivo, facilitando a identificação da origem dos logs.
logger = logging.getLogger(__name__)

# Cria a instância principal da aplicação FastAPI com metadados para a documentação automática.
app = FastAPI(
    title="DataChat RAG API",
    description="API para interagir com o chatbot de logística",
    version="1.0.0"
)

# Configura o Middleware de CORS.
# Isso é uma medida de segurança do navegador que, por padrão, bloqueia requisições
# entre diferentes "origens" (ex: localhost:3000 e localhost:8000).
# Esta configuração permite explicitamente que o nosso frontend acesse o backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Permite requisições vindas do endereço do React.
    allow_credentials=True, # Permite o envio de credenciais (cookies, etc.).
    allow_methods=["*"], # Permite todos os métodos HTTP (GET, POST, etc.).
    allow_headers=["*"], # Permite todos os cabeçalhos HTTP.
)

# Anexa as rotas definidas no arquivo `dashboard.py` à aplicação principal.
# Todas as rotas do dashboard serão acessíveis sob o prefixo "/api/dashboard".
app.include_router(dashboard.router, prefix="/api/dashboard")

# Carrega a cadeia de IA com memória UMA VEZ, quando a aplicação é iniciada.
# Isso evita o custo de recriar a cadeia a cada nova requisição, melhorando a performance.
rag_chain = create_master_chain()

# Define o formato esperado para o corpo (body) de uma requisição para o endpoint /chat.
class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None # O ID é opcional; será nulo na primeira mensagem de uma conversa.

# Registra a função `chat_endpoint` para lidar com requisições POST no endpoint /chat.
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Recebe uma pergunta e um session_id, processa na cadeia com memória
    e retorna a resposta formatada para o frontend.
    """
    # Inicia um cronômetro para medir o tempo de resposta total da cadeia.
    start_time = time.monotonic()
    
    # Loga a chegada de uma nova pergunta para facilitar o acompanhamento no terminal.
    logger.info("=================================================")
    logger.info(f"--- Nova Pergunta Recebida: '{request.question}'")
    logger.info("=================================================")

    # Lógica principal de gerenciamento de sessão:
    # Se o frontend enviou um `session_id`, usa ele.
    # Se não (é uma nova conversa), gera um novo UUID (ID único universal).
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Invoca a cadeia de IA principal.
        # Passa a pergunta do usuário como input principal.
        # Passa o `session_id` dentro do objeto `config`, que é a forma padrão do LangChain
        # de fornecer dados de configuração para cadeias que gerenciam histórico.
        full_chain_output = rag_chain.invoke(
            {"question": request.question},
            config={"configurable": {"session_id": session_id}}
        )
        
        # Extrai o dicionário de resposta formatado pela cadeia.
        response_dict = full_chain_output.get("api_response", {})
        
        # Calcula a duração total do processamento.
        end_time = time.monotonic()
        duration = end_time - start_time
        
        # Adiciona informações úteis ao dicionário de resposta.
        response_dict['response_time'] = f"{duration:.2f}"
        # Devolve o `session_id` para o frontend, para que ele possa armazená-lo e
        # enviá-lo de volta na próxima pergunta da mesma conversa.
        response_dict['session_id'] = session_id
        
        return response_dict
        
    except Exception as e:
        # Em caso de qualquer erro inesperado durante a execução da cadeia,
        # loga o erro completo no terminal e retorna uma mensagem de erro genérica.
        logger.error(f"Erro no processamento da cadeia RAG: {e}", exc_info=True)
        return {"type": "text", "content": "Desculpe, ocorreu um erro grave ao processar sua solicitação."}


# Registra a função `read_root` para lidar com requisições GET no endpoint /.
@app.get("/")
def read_root():
    """
    Endpoint de "health check" para verificar de forma simples se a API está no ar.
    Útil para monitoramento e testes de deploy.
    """
    return {"status": "DataChat API is running"}


"""
--- Exemplos de Saída do Endpoint /chat ---

A seguir estão exemplos dos diferentes tipos de JSON que este endpoint pode retornar,
dependendo da pergunta do usuário e do resultado do processamento da cadeia de IA.

# ---------------------------------------------------------------------------------
# 1. Resposta de Texto Simples
# ---------------------------------------------------------------------------------
# Ocorre em saudações, ou quando o usuário pede um dado específico que não é
# ideal para um gráfico (ex: um único status, um e-mail, etc.).

# Pergunta do Usuário: "Qual o status da operação com código de rastreio 'VV820450103ER'?"

{
    "type": "text",
    "content": "A operação com o código de rastreio 'VV820450103ER' está com o status 'EM_TRANSITO'.",
    "generated_sql": "SELECT status FROM operacoes_logisticas WHERE codigo_rastreio = 'VV820450103ER'",
    "response_time": "3.14",
    "session_id": "f9087639-1f3a-48fd-9eb7-53318fc04643"
}

# ---------------------------------------------------------------------------------
# 2. Resposta com Gráfico
# ---------------------------------------------------------------------------------
# Ocorre quando o LLM Analista de Dados determina que a melhor forma de apresentar
# a informação é através de uma visualização.

# Pergunta do Usuário: "Qual o valor total de frete agrupado por estado de destino?"

{
    "type": "chart",
    "chart_type": "bar",
    "title": "Valor Total de Frete por Estado de Destino",
    "data": [
        {
            "uf_destino": "SP",
            "valor_total_frete": 106087014.78
        },
        {
            "uf_destino": "MG",
            "valor_total_frete": 70133470.89
        },
        {
            "uf_destino": "RS",
            "valor_total_frete": 69999574.58
        }
    ],
    "x_axis": "uf_destino",
    "y_axis": [
        "valor_total_frete"
    ],
    "y_axis_label": "Valor Total Frete (R$)",
    "generated_sql": "SELECT uf_destino, SUM(valor_frete) AS valor_total_frete FROM operacoes_logisticas GROUP BY uf_destino",
    "response_time": "4.51",
    "session_id": "f9087639-1f3a-48fd-9eb7-53318fc04643"
}

# ---------------------------------------------------------------------------------
# 3. Resposta de Texto para Consulta sem Resultados
# ---------------------------------------------------------------------------------
# Ocorre quando a query SQL é válida, mas não encontra nenhum registro no banco de dados.
# O bot gera uma resposta amigável em vez de um erro.

# Pergunta do Usuário: "Qual o status da operação com código de rastreio 'NAOEXISTE123'?"

{
    "type": "text",
    "content": "Não encontrei nenhuma informação para a sua solicitação sobre a operação com código de rastreio 'NAOEXISTE123'.",
    "generated_sql": "SELECT status FROM operacoes_logisticas WHERE codigo_rastreio = 'NAOEXISTE123'",
    "response_time": "2.89",
    "session_id": "f9087639-1f3a-48fd-9eb7-53318fc04643"
}

# ---------------------------------------------------------------------------------
# 4. Resposta de Erro Grave
# ---------------------------------------------------------------------------------
# Ocorre quando uma exceção não tratada acontece durante a execução da cadeia de IA.
# O endpoint captura o erro e retorna uma mensagem genérica e segura.

{
    "type": "text",
    "content": "Desculpe, ocorreu um erro grave ao processar sua solicitação."
}

"""