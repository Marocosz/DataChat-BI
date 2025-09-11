# app/api/services/chatbot_service.py

from langchain_community.utilities import SQLDatabase
# Importamos o ChatGroq em vez do OpenAI
from langchain_groq import ChatGroq
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType

# Nossa configuração importada continua funcionando perfeitamente
from app.api.core.config import settings

class ChatbotService:
    """
    Encapsula a lógica do chatbot com LangChain e o agente SQL, usando Groq como LLM.
    """
    def __init__(self):
        # 1. Conexão com o Banco de Dados (sem alterações)
        self.db = SQLDatabase.from_uri(settings.DATABASE_URI)
        
        # 2. Inicializa o modelo de linguagem (LLM) - AGORA COM GROQ
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=settings.GROQ_API_KEY,
            # Modelos populares no Groq: "llama3-8b-8192", "mixtral-8x7b-32768"
            model_name="llama3-8b-8192", 
        )
        
        # 3. Criação do Toolkit (sem alterações)
        # O toolkit é agnóstico ao LLM, ele só precisa de um que funcione.
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        
        # 4. Criação do Agente SQL (sem alterações na lógica, apenas recebe o novo LLM)
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            verbose=True,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            prefix="""
                Você é um assistente de IA especialista em um banco de dados de catálogo.
                Seu objetivo é responder perguntas do usuário sobre os dados contidos neste catálogo.
                Dada uma pergunta, primeiro gere uma query SQL para buscar a informação e depois responda em linguagem natural.
                Sempre que possível, apresente os resultados de forma clara, como em listas ou tabelas simples.
            """
        )

    def get_response(self, user_query: str) -> str:
        """
        Processa a pergunta do usuário e retorna a resposta do agente.
        (sem alterações)
        """
        try:
            response = self.agent_executor.invoke({"input": user_query})
            return response.get("output", "Desculpe, não consegui processar sua pergunta.")
        except Exception as e:
            print(f"Ocorreu um erro na execução do agente: {e}")
            return "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde."

# A instância única do serviço continua sendo uma ótima prática
chatbot_service = ChatbotService()