# app/core/llm.py
from langchain_groq import ChatGroq
from .config import settings

def get_llm() -> ChatGroq:
    """
    Retorna uma instância configurada do LLM da Groq para geração de SQL.
    O nome do modelo é lido a partir das configurações.
    """
    return ChatGroq(
        model_name=settings.GROQ_SQL_MODEL, # <-- Lendo da configuração
        api_key=settings.GROQ_API_KEY,
        temperature=0.0
    )

def get_answer_llm() -> ChatGroq:
    """
    Retorna uma instância configurada do LLM da Groq para geração de respostas.
    O nome do modelo é lido a partir das configurações.
    """
    return ChatGroq(
        model_name=settings.GROQ_ANSWER_MODEL, # <-- Lendo da configuração
        api_key=settings.GROQ_API_KEY,
        temperature=0.3
    )