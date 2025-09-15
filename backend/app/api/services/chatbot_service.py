# backend/app/api/services/chatbot_service.py

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

CHROMA_DB_PATH = "chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ==============================================================================
# DEFINIÇÃO DOS PROMPTS PARA CADA TAREFA
# ==============================================================================

# 1. Prompt para classificar a intenção do usuário (VERSÃO MELHORADA COM EXEMPLOS)
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
CONVERSATIONAL_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "Você é um assistente de IA amigável e prestativo chamado 'Data Catalog Sage'. Responda a pergunta do usuário de forma conversacional. Responda sempre em português."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)

# 3. Prompt para a rota de RAG (com busca no banco de vetores)
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
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.1-8b-instant",
        )
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        self.vectorstore = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=self.embeddings)
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 15, 'fetch_k': 25}
        )
        
        # --- Construção das Cadeias (Chains) ---

        def format_docs(docs: List[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        classification_chain = (
            RunnableLambda(lambda x: x["question"])
            | CLASSIFICATION_PROMPT
            | self.llm
            | StrOutputParser()
        )
        conversational_chain = CONVERSATIONAL_PROMPT | self.llm | StrOutputParser()
        
        rag_chain = (
            RunnablePassthrough.assign(
                context=RunnableLambda(lambda x: x["question"]) | self.retriever | format_docs
            )
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )
        
        branch_chain = RunnablePassthrough.assign(
            topic=classification_chain
        ) | RunnableBranch(
            (lambda x: "conversacional" in x["topic"].lower(), conversational_chain),
            rag_chain,
        )
        
        # --- Gerenciamento de Memória ---
        self.session_histories: Dict[str, ChatMessageHistory] = {}
        def get_session_history(session_id: str) -> ChatMessageHistory:
            if session_id not in self.session_histories:
                self.session_histories[session_id] = ChatMessageHistory()
            return self.session_histories[session_id]

        self.conversational_chain = RunnableWithMessageHistory(
            branch_chain,
            get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

    def get_response(self, user_query: str, session_id: str) -> str:
        try:
            initial_input = {"question": user_query}
            response = self.conversational_chain.invoke(
                initial_input,
                config={"configurable": {"session_id": session_id}}
            )
            return response
        except Exception as e:
            print(f"Ocorreu um erro crítico na execução da cadeia: {e}")
            return "Ocorreu um erro inesperado ao processar sua solicitação."

chatbot_service = ChatbotService()