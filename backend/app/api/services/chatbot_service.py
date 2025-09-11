# backend/app/api/services/chatbot_service.py

from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.api.core.config import settings
from typing import Dict

SYSTEM_PROMPT = """
Você é um assistente especialista em catálogos de dados, amigável e extremamente competente.
Sua função é ajudar os usuários a entender e navegar na estrutura de um banco de dados complexo, usando um banco de dados de metadados que descreve o sistema original.

O banco de dados ao qual você tem acesso contém 3 tabelas principais:
1.  `esquemas_catalogados`: Lista os esquemas (grupos de tabelas) do banco de dados original.
2.  `tabelas_catalogadas`: Lista as tabelas do banco de dados original. A coluna `nome_negocio` contém um nome amigável para a tabela e a coluna `descricao` explica sua finalidade.
3.  `colunas_catalogadas`: Lista todas as colunas de todas as tabelas. As colunas `nome_negocio` e `descricao` são CRUCIAIS, pois explicam o que cada campo significa em termos de negócio.

Siga estas regras estritamente:
1.  **Use o Histórico da Conversa:** Sempre considere as mensagens anteriores (`chat_history`) para entender o contexto de novas perguntas.
2.  **Decida se deve usar ferramentas:** Para saudações ou perguntas gerais, simplesmente converse. Para perguntas sobre metadados (tabelas, colunas, esquemas), use suas ferramentas de banco de dados.
3.  **Raciocínio sobre Metadados:** Para perguntas como "Onde encontro o ID do cliente?", você deve raciocinar sobre os metadados para encontrar a resposta.
4.  **Seja um Tradutor:** Traduza os nomes técnicos para os nomes de negócio em suas respostas.
5.  **Responda sempre em português.**
"""

class ChatbotService:
    def __init__(self):
        self.db = SQLDatabase.from_uri(settings.DATABASE_URI)
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
        )
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.sessions: Dict[str, AgentExecutor] = {}

    def _get_or_create_agent_executor(self, session_id: str) -> AgentExecutor:
        if session_id in self.sessions:
            return self.sessions[session_id]

        memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True,
            output_key="output"
        )
        
        tools = self.toolkit.get_tools()
        
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # --- A CONSTRUÇÃO CORRETA E EXPLÍCITA ---
        # 1. Criamos o "cérebro" do agente, que sabe como usar ferramentas.
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        
        # 2. Criamos o "executor", que é o responsável por rodar o agente em loop
        #    com as ferramentas e a memória.
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
        )
        
        self.sessions[session_id] = agent_executor
        return agent_executor

    def get_response(self, user_query: str, session_id: str) -> str:
        agent_executor = self._get_or_create_agent_executor(session_id)
        try:
            response = agent_executor.invoke({"input": user_query})
            return response.get("output", "Desculpe, não consegui processar sua pergunta.")
        except Exception as e:
            print(f"Ocorreu um erro na execução do agente: {e}")
            return "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde."

chatbot_service = ChatbotService()