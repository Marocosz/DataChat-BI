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

# O armazenamento em memória é simples para desenvolvimento, 
# mas em produção considere usar Redis ou outro banco de dados.
store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    """Recupera ou cria um histórico de chat para uma dada sessão."""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def create_master_chain() -> Runnable:
    """Cria e retorna a cadeia principal de RAG com memória."""

    def trim_history(data):
        """Limita o histórico de chat para evitar exceder o limite de tokens."""
        history = data.get("chat_history", [])
        k = 6 # Mantém as últimas 6 mensagens
        if len(history) > k:
            data["chat_history"] = history[-k:]
        return data

    def format_sql_prompt(input_data):
        """Formata o histórico e preenche o prompt de geração de SQL."""
        chat_history_messages = input_data.get("chat_history", [])
        history_str = "\n".join(
            [f"{'Human' if msg.type == 'human' else 'AI'}: {msg.content}" for msg in chat_history_messages]
        )
        return SQL_PROMPT.format(
            question=input_data["question"],
            schema=input_data["schema"],
            chat_history=history_str
        )

    def execute_sql_query(query: str) -> str:
        """Executa a query SQL e adiciona um LIMIT de segurança."""
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
    
    # --- CADEIAS COMPONENTES ---

    parser = JsonOutputParser()

    # Cadeia Roteadora: Decide a intenção do usuário
    router_prompt_with_history = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", ROUTER_PROMPT.template) 
    ])
    router_chain = router_prompt_with_history | get_answer_llm() | StrOutputParser()
    
    # Cadeia de Conversa Simples: Para saudações e assuntos não relacionados a dados
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

    # Cadeia de Geração de SQL: Transforma a pergunta do usuário em SQL
    sql_generation_chain = (
        RunnablePassthrough.assign(schema=lambda _: get_compact_db_schema())
        | RunnableLambda(format_sql_prompt)
        | get_llm()
        | StrOutputParser()
    )
    
    # Cadeia de SQL Completa: Gera SQL, executa, e formata a resposta final
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

    # Cadeia de Fallback: Caso a intenção não seja reconhecida
    fallback_chain = RunnableLambda(lambda x: {"type": "text", "content": "Desculpe, não entendi sua pergunta. Pode reformular?"})

    # --- MONTAGEM DA CADEIA PRINCIPAL COM A LÓGICA DE ROTEAMENTO ---

    branch = RunnableBranch(
        (lambda x: "consulta_ao_banco_de_dados" in x["topic"], sql_chain),
        (lambda x: "saudacao_ou_conversa_simples" in x["topic"], simple_chat_chain),
        fallback_chain,
    )

    # ===================== INÍCIO DA ATUALIZAÇÃO =====================

    def format_final_output(chain_output: dict) -> dict:
        """
        Recebe a saída da branch (texto ou gráfico) e a formata em um
        dicionário com duas chaves: uma para a API e outra para o histórico.
        """
        history_content = ""
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
        | RunnableLambda(format_final_output) # Nova função de formatação
    )

    chain_with_memory = RunnableWithMessageHistory(
        main_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
        output_messages_key="history_message", # Chave correta para o histórico
    )
    
    # ===================== FIM DA ATUALIZAÇÃO =====================
    
    return chain_with_memory