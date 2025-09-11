# backend/app/api/services/chatbot_service.py

from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.api.core.config import settings
from typing import Dict, List

# ==============================================================================
# O CÉREBRO DO AGENTE: O PROMPT DO SISTEMA
# Esta é a parte mais importante. Nós damos ao agente uma persona, um contexto
# e uma metodologia de raciocínio passo a passo (Chain of Thought).
# ==============================================================================
SYSTEM_PROMPT = """
Você é o "Data Catalog Sage", um assistente de IA especialista em metadados com um raciocínio impecável.

**Sua Realidade (Regra Mais Importante):**
Você está em uma "sala de mapas". Você tem acesso a um banco de dados que é um MAPA (metadados) de um outro banco de dados muito maior, o "mundo real".
As únicas tabelas que existem nesta sala são: `esquemas_catalogados`, `tabelas_catalogadas` e `colunas_catalogadas`.
**VOCÊ NUNCA DEVE, EM HIPÓTESE ALGUMA, TENTAR EXECUTAR QUERIES EM TABELAS DO "MUNDO REAL" (ex: `TBL_DIM_CLIENTES_TEMPORE`).** Essas tabelas não existem aqui. Seu trabalho é usar o MAPA para descrever o "mundo real" para o usuário.

**Sua Missão:**
Responder a perguntas do usuário sobre o "mundo real" consultando APENAS as tabelas do seu MAPA.

**Seu Processo de Raciocínio (Obrigatório):**
1.  **Entenda a Pergunta:** O que o usuário quer saber sobre o "mundo real"?
2.  **Consulte o Mapa:** Formule a query SQL mais direta possível para encontrar a resposta nas tabelas `colunas_catalogadas` ou `tabelas_catalogadas`. Use `WHERE LIKE '%termo%'` para buscar por conceitos de negócio.
3.  **Relate o que o Mapa Diz:** Com base nos resultados da sua query no mapa, formule uma resposta para o usuário sobre como o "mundo real" é estruturado.

**Exemplo de Raciocínio Correto:**
- **Usuário:** "Quais as colunas da tabela de clientes tempore?"
- **Seu Pensamento:** "A pergunta é sobre a tabela `TBL_DIM_CLIENTES_TEMPORE` do mundo real. Para responder, eu preciso consultar o meu mapa. Vou procurar na minha tabela `colunas_catalogadas` todas as colunas cujo `tabela_id` corresponda ao id de `TBL_DIM_CLIENTES_TEMPORE` na minha tabela `tabelas_catalogadas`."
- **Sua Ação:** `sql_db_query(query="SELECT nome_negocio, descricao FROM colunas_catalogadas WHERE tabela_id = (SELECT id FROM tabelas_catalogadas WHERE nome_fisico = 'TBL_DIM_CLIENTES_TEMPORE')")`

**Regras Adicionais:**
- **Conversa Casual:** Se a pergunta for uma saudação, apenas converse, sem usar ferramentas.
- **Traduza Sempre:** Sempre use `nome_negocio` e `descricao` nas suas respostas ao usuário.
- **Não Encontrou?** Se a informação não estiver no mapa, diga: "Não encontrei essa informação no catálogo de metadados."
- **Idioma:** Responda sempre em português.
"""


class ChatbotService:
    """
    Serviço robusto para o chatbot, gerenciando sessões e executando um agente
    de raciocínio sobre metadados.
    """

    def __init__(self):
        self.db = SQLDatabase.from_uri(settings.DATABASE_URI)
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
        )
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        # Armazena os executores de agente prontos para cada sessão
        self.sessions: Dict[str, AgentExecutor] = {}

    def _get_or_create_agent_executor(self, session_id: str) -> AgentExecutor:
        """
        Recupera ou cria um AgentExecutor para uma sessão específica.
        Isso garante que cada conversa tenha sua própria memória.
        """
        if session_id in self.sessions:
            return self.sessions[session_id]

        # 1. Ferramentas que o agente pode usar (consultar DB, ver esquema, etc.)
        tools: List = self.toolkit.get_tools()

        # 2. Memória para a sessão atual
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"  # Chave de saída padrão para o executor
        )

        # 3. Prompt que define a persona, o raciocínio e o fluxo da conversa
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # 4. O "Cérebro" do Agente: decide qual ferramenta usar com base no prompt
        agent = create_tool_calling_agent(self.llm, tools, prompt)

        # 5. O Executor: roda o agente em loop com as ferramentas e a memória
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5  # Prevenção contra loops infinitos
        )

        # Armazena o executor pronto para reutilização nesta sessão
        self.sessions[session_id] = agent_executor
        return agent_executor

    def get_response(self, user_query: str, session_id: str) -> str:
        """
        Ponto de entrada principal para obter uma resposta do chatbot.
        """
        try:
            agent_executor = self._get_or_create_agent_executor(session_id)
            response = agent_executor.invoke({"input": user_query})
            return response.get("output", "Desculpe, não consegui processar sua pergunta.")
        except Exception as e:
            # Log do erro para depuração
            print(f"Ocorreu um erro crítico na execução do agente: {e}")
            # Resposta amigável para o usuário
            return "Ocorreu um erro inesperado ao processar sua solicitação. A equipe de desenvolvimento foi notificada."


# Instância única do serviço
chatbot_service = ChatbotService()
