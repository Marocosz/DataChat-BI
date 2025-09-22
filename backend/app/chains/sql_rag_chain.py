# app/chains/sql_rag_chain.py (Versão final com Parser de JSON)
import logging
import re
from typing import Dict, Any
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableBranch, RunnableLambda
from langchain_core.prompts import PromptTemplate

# Importando nossos componentes modulares
from app.core.llm import get_llm, get_answer_llm
from app.core.database import db_instance, get_compact_db_schema
from app.prompts.sql_prompts import SQL_PROMPT, FINAL_ANSWER_PROMPT, ROUTER_PROMPT

logger = logging.getLogger(__name__)

def get_sql_rag_chain() -> Runnable:
    """Cria a cadeia RAG SQL que agora retorna um dicionário parseado."""
    def execute_sql_query(query: str) -> str:
        # ... (esta função interna não muda)
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

    # Parser que garante a saída em JSON
    parser = JsonOutputParser()

    sql_generation_chain = (
        RunnablePassthrough.assign(schema=lambda _: get_compact_db_schema())
        | SQL_PROMPT
        | get_llm()
        | StrOutputParser()
    )
    
    full_rag_chain = (
        RunnablePassthrough.assign(generated_sql=sql_generation_chain)
        .assign(query_result=lambda x: execute_sql_query(x["generated_sql"]))
        | {
            "result": lambda x: x["query_result"],
            "question": lambda x: x["question"],
            # Injeta as instruções de formatação do parser no prompt
            "format_instructions": lambda x: parser.get_format_instructions(),
        }
        | FINAL_ANSWER_PROMPT
        | get_answer_llm()
        | parser # <-- O parser agora processa a saída do LLM
    )
    return full_rag_chain

def create_master_chain() -> Runnable:
    """Cria a cadeia principal com roteador onde todas as ramificações retornam um dicionário."""
    router_chain = ROUTER_PROMPT | get_answer_llm() | StrOutputParser()

    simple_chat_prompt = PromptTemplate.from_template(
        "Você é um assistente amigável chamado SuppBot. Responda a saudação do usuário de forma concisa e educada em português.\n\nUsuário: {question}\nSua Resposta:"
    )
    
    # Modificado para sempre retornar um dicionário consistente
    simple_chat_chain = (
        simple_chat_prompt 
        | get_answer_llm() 
        | StrOutputParser()
        | RunnableLambda(lambda text: {"type": "text", "content": text})
    )

    sql_chain = get_sql_rag_chain()

    fallback_chain = RunnableLambda(lambda x: {"type": "text", "content": "Desculpe, não entendi sua pergunta. Posso ajudar com dados sobre logística ou responder a saudações."})

    branch = RunnableBranch(
        (lambda x: "consulta_ao_banco_de_dados" in x["topic"], sql_chain),
        (lambda x: "saudacao_ou_conversa_simples" in x["topic"], simple_chat_chain),
        fallback_chain,
    )

    master_chain = (
        RunnablePassthrough.assign(topic=router_chain)
        | branch
    )
    
    return master_chain