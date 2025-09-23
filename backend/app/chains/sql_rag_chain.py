import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableBranch, RunnableLambda
# O import de PromptTemplate não é mais necessário aqui se não for usado diretamente
from app.core.llm import get_llm, get_answer_llm
from app.core.database import db_instance, get_compact_db_schema
from app.prompts.sql_prompts import SQL_PROMPT, FINAL_ANSWER_PROMPT, ROUTER_PROMPT

logger = logging.getLogger(__name__)

store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def create_master_chain() -> Runnable:
    def trim_history(data):
        history = data.get("chat_history", [])
        k = 6
        if len(history) > k:
            data["chat_history"] = history[-k:]
        return data

    router_prompt_with_history = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", ROUTER_PROMPT.template) 
    ])
    
    # --- CORREÇÃO PRINCIPAL AQUI ---
    # Função para formatar o histórico e preencher o FewShotPromptTemplate
    def format_sql_prompt(input_data):
        chat_history_messages = input_data.get("chat_history", [])
        history_str = "\n".join(
            [f"{'Human' if msg.type == 'human' else 'AI'}: {msg.content}" for msg in chat_history_messages]
        )
        return SQL_PROMPT.format(
            question=input_data["question"],
            schema=input_data["schema"],
            chat_history=history_str
        )
    # --------------------------------

    def execute_sql_query(query: str) -> str:
        # ... (código sem alteração)
        logger.info(f"Executando a query SQL: {query}")
        query_lower = query.lower()
        if query_lower.strip().startswith("select") and "limit" not in query_lower:
            if query.strip().endswith(';'):
                query = query.strip()[:-1] + " LIMIT 100;"
            else:
                query = query.strip() + " LIMIT 100;"
            logger.warning(f"Query modificada para incluir LIMIT: {query}")
        try:
            return db_instance.run(query)
        except Exception as e:
            logger.error(f"Erro ao executar a query: {e}")
            return f"Erro: A query falhou. Causa: {e}. Tente reformular a pergunta."
    
    parser = JsonOutputParser()

    router_chain = router_prompt_with_history | get_answer_llm() | StrOutputParser()
    
    simple_chat_prompt_with_history = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "Você é um assistente amigável chamado SuppBot...")
    ])
    simple_chat_chain = (
        simple_chat_prompt_with_history
        | get_answer_llm() 
        | StrOutputParser()
        | RunnableLambda(lambda text: {"type": "text", "content": text})
    )

    # A cadeia de SQL agora usa a nossa função de formatação manual
    sql_generation_chain = (
        RunnablePassthrough.assign(schema=lambda _: get_compact_db_schema())
        | RunnableLambda(format_sql_prompt)
        | get_llm()
        | StrOutputParser()
    )
    sql_chain = (
        RunnablePassthrough.assign(generated_sql=sql_generation_chain)
        .assign(query_result=lambda x: execute_sql_query(x["generated_sql"]))
        | {
            "result": lambda x: x["query_result"],
            "question": lambda x: x["question"],
            "format_instructions": lambda x: parser.get_format_instructions(),
        }
        | FINAL_ANSWER_PROMPT
        | get_answer_llm()
        | parser
    )

    fallback_chain = RunnableLambda(lambda x: {"type": "text", "content": "Desculpe, não entendi sua pergunta..."})

    branch = RunnableBranch(
        (lambda x: "consulta_ao_banco_de_dados" in x["topic"], sql_chain),
        (lambda x: "saudacao_ou_conversa_simples" in x["topic"], simple_chat_chain),
        fallback_chain,
    )

    main_chain = (
        RunnableLambda(trim_history)
        | RunnablePassthrough.assign(topic=router_chain) 
        | branch
    )

    chain_with_memory = RunnableWithMessageHistory(
        main_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )
    
    return chain_with_memory