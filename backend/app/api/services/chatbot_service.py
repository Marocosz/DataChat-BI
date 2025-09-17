# backend/app/api/services/chatbot_service.py

"""
O que é?
Este módulo contém a classe `ChatbotService`, que é o cérebro principal e o coração
da nossa aplicação de IA. Ele orquestra toda a lógica complexa de processamento
de linguagem natural.

Para que serve?
Sua função é receber uma pergunta do usuário e um ID de sessão, e então executar uma
cadeia (chain) de operações para gerar uma resposta inteligente. As principais
responsabilidades incluem:
1.  **Roteamento de Intenção:** Classificar se a pergunta é casual ou técnica.
2.  **RAG (Retrieval-Augmented Generation):** Buscar informações relevantes em um
    banco de vetores local (`ChromaDB`) para perguntas técnicas.
3.  **Geração de Resposta:** Usar um LLM (via Groq API) para formular uma resposta
    coerente, seja para uma conversa casual ou baseada nos dados recuperados.
4.  **Gerenciamento de Memória:** Manter o histórico de cada conversa para que o
    bot tenha contexto em interações futuras.
"""

# --- Imports Principais ---
# Componentes da Groq e LangChain para construir a lógica
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableBranch, RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.documents import Document
from typing import Dict, List
from app.api.core.config import settings

# --- Constantes de Configuração ---
# Define os caminhos e modelos para garantir consistência com o script de ingestão (ingest.py)
CHROMA_DB_PATH = "chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ==============================================================================
# DEFINIÇÃO DOS PROMPTS PARA CADA TAREFA
# ==============================================================================

# 1. Prompt para classificar a intenção do usuário (VERSÃO MELHORADA COM EXEMPLOS)
# Usamos a técnica "Few-Shot Prompting", dando exemplos concretos para o LLM.
# Isso torna a classificação muito mais precisa do que apenas dar regras.
CLASSIFICATION_PROMPT = ChatPromptTemplate.from_template(
    """Sua tarefa é classificar a pergunta do usuário como 'conversacional' ou 'rag'.
Responda APENAS com a palavra 'conversacional' ou 'rag', em minúsculas.

'conversacional' é para saudações, despedidas ou perguntas gerais que não são sobre o catálogo de dados.
'rag' é para qualquer pergunta que mencione ou se refira a tabelas, colunas, esquemas, ou conceitos de dados.

--- Exemplos ---
Pergunta: olá
Classificação: conversacional

Pergunta: obrigado pela ajuda
Classificação: conversacional

Pergunta: o que você faz?
Classificação: conversacional

Pergunta: me fale sobre a tabela de clientes
Classificação: rag

Pergunta: onde encontro o id do produto?
Classificação: rag

Pergunta: qual o tipo de dado da coluna VL_TOTAL_ITEM
Classificação: rag

Pergunta: existe alguma informação sobre faturamento?
Classificação: rag
--- Fim dos Exemplos ---

Pergunta do Usuário:
{question}

Classificação:"""
)

# 2. Prompt para a rota conversacional (sem RAG)
# Este é o prompt para a "via rápida", usado quando a IA não precisa consultar dados.
# Ele foca na persona amigável do bot e utiliza o histórico para manter uma conversa natural.
CONVERSATIONAL_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "Você é um assistente de IA amigável e prestativo chamado 'Data Catalog Sage'. Responda a pergunta do usuário de forma conversacional. Responda sempre em português."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)

# 3. Prompt para a rota de RAG (com busca no banco de vetores)
# Este prompt instrui a IA a basear sua resposta ESTRITAMENTE no {context}
# recuperado do banco de vetores, evitando que ela "alucine" ou invente informações.
RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", """Você é o "Data Catalog Sage", um assistente de IA especialista em metadados.
Sua missão é responder à pergunta do usuário da forma mais precisa possível, usando APENAS o contexto fornecido e o histórico da conversa.
Se a informação não estiver no contexto, diga "Com base nos metadados disponíveis, não encontrei uma resposta para sua pergunta."
Responda sempre em português."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "CONTEXTO DOS METADADOS:\n{context}\n\nPERGUNTA:\n{question}"),
    ]
)


class ChatbotService:
    def __init__(self):
        # Inicializa o LLM (Large Language Model) da Groq.
        # Este é o "cérebro" que gera o texto das respostas.
        self.llm = ChatGroq(
            temperature=0,  # Baixa temperatura para respostas mais factuais e menos criativas.
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.1-8b-instant",
        )
        
        # Inicializa o modelo de embedding.
        # Este modelo transforma texto (perguntas e documentos) em vetores numéricos para busca de similaridade.
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        # Carrega o banco de vetores Chroma, que já foi criado e salvo no disco pelo ingest.py.
        self.vectorstore = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=self.embeddings)
        
        # Cria o componente "retriever", responsável por executar as buscas no banco de vetores.
        # Usamos o tipo de busca "mmr" para garantir resultados relevantes E diversos.
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 15, 'fetch_k': 25} # Busca 25 docs e seleciona os 15 mais diversos.
        )
        
        # --- Construção das Cadeias Lógicas (Chains) usando LCEL ---

        # Função auxiliar para converter a lista de documentos do retriever em uma única string de texto.
        def format_docs(docs: List[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        # Cadeia 1: O Classificador. Recebe a pergunta, a classifica e retorna "conversacional" ou "rag".
        classification_chain = (
            RunnableLambda(lambda x: x["question"])  # Extrai apenas a pergunta do dicionário de entrada.
            | CLASSIFICATION_PROMPT
            | self.llm
            | StrOutputParser() # Garante que a saída seja uma string simples.
        )
        
        # Cadeia 2: A rota de Conversa. É uma cadeia simples que não faz busca de dados.
        conversational_chain = CONVERSATIONAL_PROMPT | self.llm | StrOutputParser()
        
        # Cadeia 3: A rota de RAG. Esta é a cadeia de trabalho pesado.
        rag_chain = (
            # RunnablePassthrough.assign permite adicionar uma nova chave ao dicionário de dados.
            # Aqui, criamos a chave "context" executando uma sub-cadeia.
            RunnablePassthrough.assign(
                # A sub-cadeia primeiro extrai a pergunta, depois passa para o retriever, e formata o resultado.
                context=RunnableLambda(lambda x: x["question"]) | self.retriever | format_docs
            )
            | RAG_PROMPT # O dicionário completo (com context, question, etc.) é passado para o prompt.
            | self.llm
            | StrOutputParser()
        )
        
        # Cadeia 4: O Roteador. Ele decide qual das cadeias acima executar.
        branch_chain = RunnablePassthrough.assign(
            # Primeiro, roda o classificador e adiciona sua resposta como a chave "topic".
            topic=classification_chain
        ) | RunnableBranch(
            # Uma tupla (condição, cadeia). Se a condição for verdadeira, executa a cadeia.
            (lambda x: "conversacional" in x["topic"].lower(), conversational_chain),
            # Se nenhuma condição for atendida, esta é a cadeia padrão a ser executada.
            rag_chain,
        )
        
        # --- Gerenciamento de Memória ---
        # Um dicionário simples para armazenar o histórico de cada sessão de chat.
        self.session_histories: Dict[str, ChatMessageHistory] = {}
        def get_session_history(session_id: str) -> ChatMessageHistory:
            # Se for a primeira mensagem de uma sessão, cria um novo histórico.
            if session_id not in self.session_histories:
                self.session_histories[session_id] = ChatMessageHistory()
            # Retorna o histórico correspondente ao ID da sessão.
            return self.session_histories[session_id]

        # Monta a cadeia conversacional final, "empacotando" nosso roteador com a capacidade de memória.
        # Ela gerencia automaticamente o carregamento do histórico antes da execução e o salvamento depois.
        self.conversational_chain = RunnableWithMessageHistory(
            branch_chain,
            get_session_history,
            input_messages_key="question", # Chave de entrada que contém a pergunta do usuário.
            history_messages_key="chat_history", # Chave que o prompt espera para o histórico.
        )

    def get_response(self, user_query: str, session_id: str) -> str:
        # Ponto de entrada público que será chamado pelo endpoint da API.
        try:
            # O input para a cadeia com memória precisa ser um dicionário.
            initial_input = {"question": user_query}
            # Invoca a cadeia completa, passando o input e a configuração da sessão.
            response = self.conversational_chain.invoke(
                initial_input,
                config={"configurable": {"session_id": session_id}}
            )
            return response
        except Exception as e:
            # Rede de segurança para capturar qualquer erro inesperado durante a execução.
            print(f"Ocorreu um erro crítico na execução da cadeia: {e}")
            return "Ocorreu um erro inesperado ao processar sua solicitação."

# Cria a instância única do serviço (padrão Singleton).
# Isso é eficiente pois os modelos e o banco de vetores são carregados apenas uma vez,
# quando o servidor da API é iniciado.
chatbot_service = ChatbotService()