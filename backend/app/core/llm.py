# app/core/llm.py
from langchain_groq import ChatGroq
from .config import settings

def get_llm() -> ChatGroq:
    """
    Retorna uma instância configurada do LLM da Groq para geração de SQL.
    - model_name: Modelo potente para raciocínio e geração de SQL.
    - temperature=0.0: Essencial para obter queries SQL determinísticas e precisas.
    """
    return ChatGroq(
        model_name="llama3-70b-8192",
        api_key=settings.GROQ_API_KEY,
        temperature=0.0
    )

def get_answer_llm() -> ChatGroq:
    """
    Retorna uma instância configurada do LLM da Groq para geração de respostas.
    - model_name: Pode ser um modelo mais rápido para respostas em linguagem natural.
    - temperature=0.3: Um pouco de criatividade para uma resposta mais fluida.
    """
    return ChatGroq(
        model_name="llama3-8b-8192",
        api_key=settings.GROQ_API_KEY,
        temperature=0.3
    )