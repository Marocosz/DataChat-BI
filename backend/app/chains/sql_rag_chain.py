# =============================================================================
# ARQUIVO DE ORQUESTRAÇÃO DAS CADEIAS (CHAINS)
#
# Este é o módulo mais importante da nossa lógica de IA. Ele é responsável por
# construir e conectar todas as peças do quebra-cabeça:
# 1. A cadeia RAG que gera e executa SQL.
# 2. A cadeia de Roteamento que classifica a intenção do usuário.
# 3. A cadeia de Bate-papo Simples para saudações.
# 4. A Cadeia Mestre, que une tudo em um fluxo de trabalho inteligente e condicional.
#
# Utilizamos a LangChain Expression Language (LCEL), com o operador pipe "|",
# para compor essas cadeias de forma declarativa e legível.
# =============================================================================

# --- Bloco de Importações ---
import logging
import re
from typing import Dict, Any
# Componentes do LangChain para construir as cadeias e processar as saídas.
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableBranch, RunnableLambda
from langchain_core.prompts import PromptTemplate

# Importando nossos componentes modulares customizados.
from app.core.llm import get_llm, get_answer_llm
from app.core.database import db_instance, get_compact_db_schema
from app.prompts.sql_prompts import SQL_PROMPT, FINAL_ANSWER_PROMPT, ROUTER_PROMPT

# Instancia um logger para este módulo.
logger = logging.getLogger(__name__)


# --- CADEIA RAG SQL: A LÓGICA PARA CONSULTAS AO BANCO DE DADOS ---
def get_sql_rag_chain() -> Runnable:
    """
    Cria a cadeia RAG SQL completa, responsável por transformar uma pergunta
    em uma consulta SQL, executá-la e formatar o resultado final em JSON.
    """
    
    # Define uma função interna para executar a query de forma segura.
    def execute_sql_query(query: str) -> str:
        logger.info(f"Executando a query SQL: {query}")
        query_lower = query.lower()
        
        # Lógica de segurança: Adiciona um LIMIT a qualquer query SELECT que não o possua.
        # Isso previne que a IA acidentalmente peça dados demais, o que causaria
        # o erro 413 (Request Entity Too Large) na segunda chamada ao LLM.
        if query_lower.strip().startswith("select") and "limit" not in query_lower:
            if query.strip().endswith(';'):
                query = query.strip()[:-1] + " LIMIT 100;"
            else:
                query = query.strip() + " LIMIT 100;"
                
            logger.warning(f"Query modificada para incluir LIMIT: {query}")
        
        try:
            # Usa a instância de conexão do LangChain para rodar a query.
            return db_instance.run(query)
        
        except Exception as e:
            logger.error(f"Erro ao executar a query: {e}")
            return f"Erro: A query falhou. Causa: {e}. Tente reformular a pergunta."

    # Instancia o parser que forçará a saída do LLM final para o formato JSON.
    parser = JsonOutputParser()

    # Cadeia para Geração de SQL
    sql_generation_chain = (
        # Começa com a entrada original e injeta o schema do banco de dados no fluxo.
        RunnablePassthrough.assign(schema=lambda _: get_compact_db_schema())
        # Passa o dicionário (pergunta + schema) para o prompt de SQL.
        | SQL_PROMPT
        # Envia o prompt preenchido para o LLM potente.
        | get_llm()
        # Pega a saída do LLM e a limpa, retornando uma string de SQL pura.
        | StrOutputParser()
    )
    
    # Cadeia Completa que Executa e Formata
    full_rag_chain = (
        # Começa com a entrada original e adiciona a 'generated_sql' vinda da cadeia acima.
        RunnablePassthrough.assign(generated_sql=sql_generation_chain)
        # Pega o dicionário e adiciona o 'query_result' ao executar o SQL gerado.
        .assign(query_result=lambda x: execute_sql_query(x["generated_sql"]))
        # Reorganiza o dicionário para casar com as variáveis do prompt final.
        | {
            "result": lambda x: x["query_result"],
            "question": lambda x: x["question"],
            # Injeta as instruções de formatação do parser no prompt para guiar o LLM.
            "format_instructions": lambda x: parser.get_format_instructions(),
        }
        # Preenche o prompt final com o resultado do banco e as instruções.
        | FINAL_ANSWER_PROMPT
        # Envia o prompt para o LLM rápido para gerar a resposta final.
        | get_answer_llm()
        # Usa o parser para garantir que a resposta final seja um JSON válido.
        | parser
    )
    return full_rag_chain


# --- CADEIA MESTRE: O ORQUESTRADOR PRINCIPAL DA APLICAÇÃO ---
def create_master_chain() -> Runnable:
    """
    Cria a cadeia principal que primeiro roteia a intenção do usuário e depois
    executa a cadeia apropriada (SQL RAG ou Chat Simples).
    """
    # Cadeia do Roteador: Uma chamada rápida para classificar a pergunta.
    router_chain = ROUTER_PROMPT | get_answer_llm() | StrOutputParser()

    # Cadeia de Chat Simples: Para responder a saudações e conversas simples.
    simple_chat_prompt = PromptTemplate.from_template(
        "Você é um assistente amigável chamado SuppBot. Responda a saudação do usuário de forma concisa e educada em português.\n\nUsuário: {question}\nSua Resposta:"
    )
    
    # Esta cadeia é modificada para sempre retornar um dicionário, mantendo o formato de saída
    # consistente com as outras ramificações do roteador.
    simple_chat_chain = (
        simple_chat_prompt 
        | get_answer_llm() 
        | StrOutputParser()
        # Transforma a string de texto em um dicionário no formato esperado pelo frontend.
        | RunnableLambda(lambda text: {"type": "text", "content": text})
    )

    # Cadeia RAG SQL: Reutiliza a função complexa que definimos acima.
    sql_chain = get_sql_rag_chain()

    # Cadeia de Fallback: Uma "saída de emergência" se o roteador não conseguir classificar a pergunta.
    fallback_chain = RunnableLambda(lambda x: {"type": "text", "content": "Desculpe, não entendi sua pergunta. Posso ajudar com dados sobre logística ou responder a saudações."})

    # O Roteador Condicional (RunnableBranch)
    # Funciona como um if/elif/else. Ele verifica cada condição em ordem e executa a primeira que for verdadeira.
    branch = RunnableBranch(
        # Condição 1: Se o 'topic' contiver "consulta_ao_banco_de_dados", executa a 'sql_chain'.
        (lambda x: "consulta_ao_banco_de_dados" in x["topic"], sql_chain),
        # Condição 2: Se o 'topic' contiver "saudacao_ou_conversa_simples", executa a 'simple_chat_chain'.
        (lambda x: "saudacao_ou_conversa_simples" in x["topic"], simple_chat_chain),
        # Else: Se nenhuma condição for atendida, executa a 'fallback_chain'.
        fallback_chain,
    )

    # A Cadeia Mestre que Une Tudo
    master_chain = (
        # Pega a entrada original ({"question": ...}), executa a 'router_chain' para obter o 'topic',
        # e passa um novo dicionário ({"question": ..., "topic": ...}) para a próxima etapa.
        RunnablePassthrough.assign(topic=router_chain)
        # O 'branch' recebe o dicionário com a pergunta e o tópico e decide qual caminho seguir.
        | branch
    )
    
    return master_chain