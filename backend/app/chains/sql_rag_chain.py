# app/chains/sql_rag_chain.py
import logging
from typing import Dict, Any
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough

# Importando nossos componentes modulares
from app.core.llm import get_llm, get_answer_llm
from app.core.database import db_instance
from app.prompts.sql_prompts import SQL_PROMPT, FINAL_ANSWER_PROMPT

logger = logging.getLogger(__name__)

def execute_sql_query(query: str) -> str:
    """Executa a query SQL e trata possíveis erros."""
    logger.info(f"Executando a query SQL: {query}")
    try:
        return db_instance.run(query)
    except Exception as e:
        logger.error(f"Erro ao executar a query: {e}")
        return f"Erro: A query falhou. Causa: {e}. Tente reformular a pergunta."

def get_sql_rag_chain() -> Runnable:
    """
    Constrói e retorna a cadeia RAG completa usando LangChain Expression Language (LCEL).
    """
    # Cadeia para geração de SQL
    sql_generation_chain = (
        RunnablePassthrough.assign(schema=lambda _: db_instance.table_info)
        | SQL_PROMPT
        | get_llm()
        | StrOutputParser()
    )

    # Cadeia completa que orquestra o fluxo
    full_rag_chain = (
        RunnablePassthrough.assign(
            generated_sql=sql_generation_chain  # 1. Gera SQL
        ).assign(
            query_result=lambda x: execute_sql_query(x["generated_sql"])  # 2. Executa SQL
        )
        | {
            "result": lambda x: x["query_result"],
            "question": lambda x: x["question"],
        }
        | FINAL_ANSWER_PROMPT  # 3. Prepara prompt final
        | get_answer_llm()      # 4. Gera resposta em linguagem natural
        | StrOutputParser()
    )
    
    return full_rag_chain