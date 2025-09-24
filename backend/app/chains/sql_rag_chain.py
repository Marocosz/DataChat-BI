# ================================================================================================================
# ================================================================================================================
#
# Visão Geral do Módulo
#
# Este arquivo Python implementa uma cadeia de processamento de linguagem natural (NLP) complexa,
# com foco em interações de chatbot que podem responder tanto a perguntas gerais quanto a perguntas
# que exigem a consulta de um banco de dados SQL. A arquitetura central utiliza a biblioteca
# LangChain para orquestrar uma série de passos lógicos, incluindo:
#
# 1. Gerenciamento de Estado Avançado: Um dicionário (`store`) armazena o histórico de mensagens e
#    a última consulta SQL executada para cada sessão de usuário. Isso permite que o sistema
#    mantenha o contexto e referencie consultas anteriores, o que é crucial para perguntas de seguimento.
#
# 2. Roteamento Inteligente: A cadeia começa com um "roteador" (`router_chain`) que analisa a intenção
#    do usuário (se a pergunta é uma saudação, uma conversa simples, ou se requer uma consulta ao banco de dados).
#
# 3. Geração e Execução de SQL: Se a intenção for uma consulta ao banco de dados, uma sub-cadeia
#    especializada (`sql_chain`) é ativada. Ela gera uma query SQL com base na pergunta do usuário e
#    no esquema do banco de dados, executa essa query e formata o resultado.
#
# 4. Resposta Final: O resultado da consulta SQL é então usado como contexto para um segundo modelo de
#    linguagem grande (LLM) que gera uma resposta final em linguagem natural para o usuário.
#
# 5. Memória de Conversa: A cadeia principal é envolvida por `RunnableWithMessageHistory`, que gerencia
#    o histórico de mensagens, permitindo que a IA mantenha o contexto da conversa.
#
# A lógica de programação foi estruturada para ser modular e extensível, com funções dedicadas para cada
# etapa, como a execução segura de queries SQL (`execute_sql_query`) e a formatação da saída final
# (`format_final_output`). O uso de `RunnableBranch` permite a tomada de decisões dinâmicas, direcionando
# a conversa para a cadeia apropriada.
#
# ================================================================================================================
# ================================================================================================================

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

# O 'store' guarda um dicionário para cada sessão,
# contendo o histórico de mensagens e a última query SQL.
store = {}

def get_session_data(session_id: str) -> dict:
    """
    Recupera ou cria um dicionário de dados para uma sessão de usuário.

    Args:
        session_id: O identificador único da sessão.

    Returns:
        Um dicionário contendo o histórico de mensagens e a última query SQL.
    """
    # Se a sessão ainda não existir no 'store', cria uma nova entrada com um histórico vazio
    # e um marcador para a última SQL.
    if session_id not in store:
        store[session_id] = {
            "history": ChatMessageHistory(),
            "last_sql": "Nenhuma query foi executada ainda."
        }
    return store[session_id]

def get_session_history(session_id: str) -> ChatMessageHistory:
    """
    Função auxiliar para a classe RunnableWithMessageHistory que retorna o histórico
    de mensagens de uma sessão específica.

    Args:
        session_id: O identificador da sessão.

    Returns:
        Uma instância de ChatMessageHistory.
    """
    return get_session_data(session_id)["history"]

def update_last_sql(session_id: str, sql: str):
    """
    Atualiza a última query SQL executada para uma sessão.

    Esta função é chamada após a execução de uma query para persistir a informação
    no estado da sessão, permitindo que o LLM a utilize como contexto para
    perguntas de seguimento.

    Args:
        session_id: O identificador da sessão.
        sql: A string da query SQL executada.
    """
    if session_id in store:
        # A atualização só ocorre se a query não for vazia ou conter um erro
        if sql and "erro:" not in sql.lower():
            logger.info(f"Atualizando last_sql para a sessão {session_id}: {sql}")
            store[session_id]["last_sql"] = sql


def create_master_chain() -> Runnable:
    """
    Cria e retorna a cadeia principal de LangChain, que orquestra todo o fluxo
    de conversa, desde o roteamento da pergunta até a geração da resposta final.

    Returns:
        Uma instância de Runnable, pronta para ser invocada com uma pergunta do usuário.
    """

    def trim_history(data):
        """
        Função para limitar o histórico de chat.
        Isso é crucial para evitar exceder o limite de tokens do modelo de linguagem,
        mantendo apenas as mensagens mais recentes e relevantes.
        """
        history = data.get("chat_history", [])
        k = 6
        if len(history) > k:
            data["chat_history"] = history[-k:]
        return data

    def execute_sql_query(query: str) -> str:
        """
        Executa a query SQL de forma segura, adicionando um LIMIT e tratando erros.

        Args:
            query: A query SQL a ser executada.

        Returns:
            Uma string com o resultado da query, um erro ou uma mensagem de resultado vazio.
        """
        logger.info(f"Executando a query SQL: {query}")
        query_lower = query.lower()

        is_aggregation = any(agg in query_lower for agg in ["count(", "sum(", "avg("])
        has_group_by = "group by" in query_lower
        has_limit = "limit" in query_lower

        # Adiciona 'LIMIT 100' à query para evitar a recuperação de um grande número de registros,
        # a menos que seja uma agregação ou já contenha um limite.
        if query_lower.strip().startswith("select") and not has_limit:
            if not is_aggregation or has_group_by:
                if query.strip().endswith(';'):
                    query = query.strip()[:-1] + " LIMIT 100;"
                else:
                    query = query.strip() + " LIMIT 100;"
                logger.warning(f"Query modificada para incluir LIMIT: {query}")
                
        try:
            # Executa a query através da instância do banco de dados do LangChain
            result = db_instance.run(query, include_columns=True)
            
            # Verifica se o resultado retornado é vazio, que é representado como '[]'
            if not result or result == '[]':
                logger.warning("Query retornou resultado vazio. Informando ao LLM.")
                return "RESULTADO_VAZIO: Nenhuma informação encontrada para a sua solicitação."
            
            logger.info(f"===> RESULTADO BRUTO DO DB (VIA LANGCHAIN): {result!r}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao executar a query: {e}")
            return f"ERRO_DB: A query falhou. Causa: {e}. Tente reformular a pergunta."
    
    # Define o parser para formatar a saída final como JSON
    parser = JsonOutputParser()

    # Cadeia para o roteador, que decide o caminho a seguir com base na pergunta
    router_prompt_with_history = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", ROUTER_PROMPT.template) 
    ])
    router_chain = router_prompt_with_history | get_answer_llm() | StrOutputParser()
    
    # Cadeia para conversas simples que não precisam de consulta ao banco de dados
    simple_chat_prompt_with_history = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "Você é um assistente amigável chamado SuppBot. Responda de forma concisa e útil.")
    ])
    simple_chat_chain = (
        simple_chat_prompt_with_history
        | get_answer_llm() 
        | StrOutputParser()
        # Formata a saída como um dicionário para manter a consistência com a cadeia SQL
        | RunnableLambda(lambda text: {"type": "text", "content": text})
    )

    # Cadeia de Geração de SQL: utiliza o esquema do banco e o histórico para gerar a query
    sql_generation_chain = (
        RunnablePassthrough.assign(
            # Passa o esquema do banco de dados para o prompt
            schema=lambda _: get_compact_db_schema(),
            # Injeta a última SQL executada como contexto para o LLM
            previous_sql=lambda _, config: get_session_data(config["configurable"]["session_id"]).get("last_sql", "N/A")
        )
        | SQL_PROMPT
        | get_llm()
        | StrOutputParser()
    )
    
    def execute_and_log_query(data: dict) -> str:
        """
        Função para executar a query SQL e retornar o resultado.
        A query gerada é extraída do dicionário de dados (`data`).
        """
        query = data["generated_sql"]
        result = execute_sql_query(query)
        logger.info(f"===> RESULTADO BRUTO DO DB (VIA LANGCHAIN): {result!r}")
        return result

    # Cadeia de SQL Completa: Gerencia a geração, execução e formatação da resposta
    sql_chain = (
        RunnablePassthrough.assign(generated_sql=sql_generation_chain)
        .assign(
            # Executa a query gerada e armazena o resultado em `query_result`
            query_result=execute_and_log_query,
            # Chama a função para atualizar a última SQL na sessão do usuário
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

    # Cadeia de fallback para quando a pergunta não se encaixa em nenhuma categoria
    fallback_chain = RunnableLambda(lambda x: {"type": "text", "content": "Desculpe, não entendi sua pergunta. Pode reformular?"})

    # A lógica de roteamento principal, que direciona para a cadeia correta
    branch = RunnableBranch(
        # Se a intenção for 'consulta_ao_banco_de_dados', usa a cadeia SQL
        (lambda x: "consulta_ao_banco_de_dados" in x["topic"], sql_chain),
        # Se for 'saudacao_ou_conversa_simples', usa a cadeia de chat simples
        (lambda x: "saudacao_ou_conversa_simples" in x["topic"], simple_chat_chain),
        # Caso contrário, usa a cadeia de fallback
        fallback_chain,
    )

    def format_final_output(chain_output: dict) -> dict:
        """
        Formata a saída final da cadeia para ser consumida pela API e pelo histórico.

        Args:
            chain_output: O dicionário de saída da cadeia anterior.

        Returns:
            Um dicionário com a resposta da API e a mensagem a ser adicionada ao histórico.
        """
        history_content = ""
        if isinstance(chain_output, dict):
            # Extrai o conteúdo da resposta para o histórico, dependendo do tipo (texto ou gráfico)
            if chain_output.get("type") == "text":
                history_content = chain_output.get("content", "Não foi possível gerar uma resposta.")
            elif chain_output.get("type") == "chart":
                title = chain_output.get("title", "sem título")
                history_content = f"Gerei um gráfico para você sobre: '{title}'"
        
        return {
            "api_response": chain_output, 
            "history_message": history_content
        }

    # A cadeia principal que encadeia todos os passos
    main_chain = (
        RunnableLambda(trim_history)
        | RunnablePassthrough.assign(topic=router_chain) 
        | branch
        | RunnableLambda(format_final_output)
    )

    # Envolve a cadeia principal com o gerenciamento de histórico
    chain_with_memory = RunnableWithMessageHistory(
        main_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
        output_messages_key="history_message",
    )
    
    return chain_with_memory