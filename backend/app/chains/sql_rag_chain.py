import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableBranch, RunnableLambda
from app.core.llm import get_llm, get_answer_llm
from app.core.database import db_instance, get_compact_db_schema
from app.prompts.sql_prompts import SQL_PROMPT, FINAL_ANSWER_PROMPT, ROUTER_PROMPT

logger = logging.getLogger(__name__)

# --- INÍCIO DA ATUALIZAÇÃO: Gerenciamento de Estado Avançado ---

# O 'store' agora vai guardar um dicionário para cada sessão,
# contendo tanto o histórico de mensagens quanto a última query SQL.
store = {}

def get_session_data(session_id: str) -> dict:
    """Recupera ou cria os dados de uma sessão."""
    if session_id not in store:
        store[session_id] = {
            "history": ChatMessageHistory(),
            "last_sql": "Nenhuma query foi executada ainda."
        }
    return store[session_id]

def get_session_history(session_id: str) -> ChatMessageHistory:
    """Função compatível com RunnableWithMessageHistory para pegar apenas o histórico."""
    return get_session_data(session_id)["history"]

def update_last_sql(session_id: str, sql: str):
    """Atualiza a última query SQL para uma sessão."""
    if session_id in store:
        # Só atualiza se o SQL gerado não for um erro ou texto vazio
        if sql and "erro:" not in sql.lower():
            logger.info(f"Atualizando last_sql para a sessão {session_id}: {sql}")
            store[session_id]["last_sql"] = sql

# --- FIM DA ATUALIZAÇÃO ---


def create_master_chain() -> Runnable:
    """Cria e retorna a cadeia principal de RAG com memória."""

    def trim_history(data):
        """Limita o histórico de chat para evitar exceder o limite de tokens."""
        history = data.get("chat_history", [])
        k = 6 # Mantém as últimas 6 mensagens
        if len(history) > k:
            data["chat_history"] = history[-k:]
        return data

    def execute_sql_query(query: str) -> str:
        """Executa a query SQL e adiciona um LIMIT de segurança."""
        logger.info(f"Executando a query SQL: {query}")
        query_lower = query.lower()
        # Refinamento: Não adicionar LIMIT se já existir ou for agregação sem GROUP BY
        is_aggregation = any(agg in query_lower for agg in ["count(", "sum(", "avg("])
        has_group_by = "group by" in query_lower

        if query_lower.strip().startswith("select") and "limit" not in query_lower:
            if not is_aggregation or has_group_by:
                if query.strip().endswith(';'):
                    query = query.strip()[:-1] + " LIMIT 100;"
                else:
                    query = query.strip() + " LIMIT 100;"
                logger.warning(f"Query modificada para incluir LIMIT: {query}")
        try:
            return db_instance.run(query, include_columns=True)
        except Exception as e:
            logger.error(f"Erro ao executar a query: {e}")
            return f"Erro: A query falhou. Causa: {e}. Tente reformular a pergunta."
    
    parser = JsonOutputParser()

    router_prompt_with_history = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", ROUTER_PROMPT.template) 
    ])
    router_chain = router_prompt_with_history | get_answer_llm() | StrOutputParser()
    
    simple_chat_prompt_with_history = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "Você é um assistente amigável chamado SuppBot. Responda de forma concisa e útil.")
    ])
    simple_chat_chain = (
        simple_chat_prompt_with_history
        | get_answer_llm() 
        | StrOutputParser()
        | RunnableLambda(lambda text: {"type": "text", "content": text})
    )

    # --- INÍCIO DA ATUALIZAÇÃO: Injetando a Última SQL na Cadeia ---

    # Cadeia de Geração de SQL: Agora usa o novo SQL_PROMPT e injeta a 'previous_sql'.
    sql_generation_chain = (
        RunnablePassthrough.assign(
            schema=lambda _: get_compact_db_schema(),
            # Pega a 'session_id' que o LangChain passa no 'config'
            # e usa nossa função para buscar a última SQL da sessão correta.
            previous_sql=lambda _, config: get_session_data(config["configurable"]["session_id"]).get("last_sql", "N/A")
        )
        | SQL_PROMPT # Nosso prompt atualizado que agora usa 'previous_sql'
        | get_llm()
        | StrOutputParser()
    )
    
    def execute_and_log_query(data: dict) -> str:
        """Executa a query e loga o resultado bruto retornado pelo LangChain."""
        query = data["generated_sql"]
        result = execute_sql_query(query)
        # A linha mais importante do nosso debug:
        logger.info(f"===> RESULTADO BRUTO DO DB (VIA LANGCHAIN): {result!r}")
        return result

    # Cadeia de SQL Completa: Agora com passo extra para logar o resultado.
    sql_chain = (
        RunnablePassthrough.assign(generated_sql=sql_generation_chain)
        .assign(
            # Usamos nossa nova função aqui para capturar e logar o resultado
            query_result=execute_and_log_query,
            _update_sql=lambda x, config: update_last_sql(config["configurable"]["session_id"], x["generated_sql"])
        )
        | {
            "result": lambda x: x["query_result"],
            "question": lambda x: x["question"],
            "format_instructions": lambda x: parser.get_format_instructions(),
        }
        | FINAL_ANSWER_PROMPT
        | get_answer_llm()
        | parser
    )

    # --- FIM DA ATUALIZAÇÃO ---

    fallback_chain = RunnableLambda(lambda x: {"type": "text", "content": "Desculpe, não entendi sua pergunta. Pode reformular?"})

    branch = RunnableBranch(
        (lambda x: "consulta_ao_banco_de_dados" in x["topic"], sql_chain),
        (lambda x: "saudacao_ou_conversa_simples" in x["topic"], simple_chat_chain),
        fallback_chain,
    )

    def format_final_output(chain_output: dict) -> dict:
        history_content = ""
        if isinstance(chain_output, dict):
            if chain_output.get("type") == "text":
                history_content = chain_output.get("content", "Não foi possível gerar uma resposta.")
            elif chain_output.get("type") == "chart":
                title = chain_output.get("title", "sem título")
                history_content = f"Gerei um gráfico para você sobre: '{title}'"
        
        return {
            "api_response": chain_output, 
            "history_message": history_content
        }

    main_chain = (
        RunnableLambda(trim_history)
        | RunnablePassthrough.assign(topic=router_chain) 
        | branch
        | RunnableLambda(format_final_output)
    )

    chain_with_memory = RunnableWithMessageHistory(
        main_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
        output_messages_key="history_message",
    )
    
    return chain_with_memory