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
#    a última consulta SQL executada para cada sessão de usuário.
#
# 2. Roteamento Inteligente: A cadeia começa com um "roteador" (`router_chain`) que analisa a intenção
#    do usuário.
#
# 3. Reescrita de Pergunta (Rephraser): Antes de gerar o SQL, um passo intermediário reescreve perguntas
#    ambíguas (ex: "e para ele?") em perguntas completas e autônomas, usando o histórico da conversa.
#
# 4. Geração e Execução de SQL: Uma sub-cadeia especializada (`sql_chain`) gera uma query SQL com base
#    na pergunta reescrita e no esquema do banco, executa essa query e formata o resultado.
#
# 5. Resposta Final: O resultado da consulta SQL é usado para gerar uma resposta final em linguagem natural.
#
# 6. Memória de Conversa: A cadeia principal é envolvida por `RunnableWithMessageHistory`, que gerencia
#    automaticamente o histórico de mensagens.
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
### NOVA LÓGICA: REPHRASER ###
# Importa o novo REPHRASER_PROMPT junto com os outros.
from app.prompts.sql_prompts import SQL_PROMPT, FINAL_ANSWER_PROMPT, ROUTER_PROMPT, REPHRASER_PROMPT

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
    no estado da sessão.

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
    
    def format_simple_chat_output(text_content: str) -> dict:
        """Adiciona uma chave 'generated_sql' à saída do chat simples para manter a estrutura de dados consistente."""
        return {
            "type": "text",
            "content": text_content,
            "generated_sql": "Nenhuma query foi necessária para esta resposta."
        }

    # Cadeia para conversas simples que não precisam de consulta ao banco de dados
    simple_chat_prompt_with_history = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "Você é um assistente amigável chamado SuppBot. Responda de forma concisa e útil.")
    ])
    simple_chat_chain = (
        simple_chat_prompt_with_history
        | get_answer_llm() 
        | StrOutputParser()
        | RunnableLambda(format_simple_chat_output)
    )

    ### NOVA LÓGICA: REPHRASER ###
    # 1. Cria a cadeia do "Especialista em Contexto" (Rephraser)
    # A tarefa dele é transformar uma pergunta ambígua em uma pergunta completa.
    rephrasing_chain = (
        {
            "question": lambda x: x["question"],
            "chat_history": lambda x: x["chat_history"]
        }
        | REPHRASER_PROMPT
        | get_answer_llm()
        | StrOutputParser()
    )

    # 2. Cadeia de Geração de SQL: agora é MUITO MAIS SIMPLES.
    # Ela não precisa mais de `chat_history` ou `previous_sql`, pois sempre
    # receberá uma pergunta completa e autônoma do Rephraser.
    sql_generation_chain = (
        RunnablePassthrough.assign(
            schema=lambda _: get_compact_db_schema()
        )
        # IMPORTANTE: Seu SQL_PROMPT em sql_prompts.py deve ser simplificado
        # para receber apenas {question} e {schema}.
        | SQL_PROMPT
        | get_llm()
        | StrOutputParser()
    )
    
    def execute_and_log_query(data: dict) -> str:
        query = data["generated_sql"]
        result = execute_sql_query(query)
        logger.info(f"===> RESULTADO BRUTO DO DB (VIA LANGCHAIN): {result!r}")
        return result

    # Cadeia que gera a resposta final (texto ou gráfico)
    final_response_chain = (
        {
            "result": lambda x: x["query_result"],
            "question": lambda x: x["question"], # Receberá a pergunta já reescrita
            "format_instructions": lambda x: parser.get_format_instructions(),
        }
        | FINAL_ANSWER_PROMPT
        | get_answer_llm()
        | parser
    )

    def combine_sql_with_response(data: dict) -> dict:
        """Pega a resposta final (texto/gráfico) e adiciona a chave 'generated_sql' a ela."""
        final_json_response = data["final_response_json"]
        final_json_response["generated_sql"] = data["generated_sql"]
        return final_json_response

    # 3. Monta a nova `sql_chain` com o passo de reescrita no início
    sql_chain = (
        # Passo 1: Invoca o Rephraser para obter uma pergunta clara e autônoma.
        RunnablePassthrough.assign(
            standalone_question=rephrasing_chain
        ).assign(
            # Adiciona um log para vermos a pergunta reescrita. Ótimo para debug!
            _log_standalone_question=RunnableLambda(
                lambda x: logger.info(f"Pergunta Reescrita pelo Rephraser: '{x['standalone_question']}'")
            )
        )
        # Passo 2: Gera o SQL usando APENAS a pergunta autônoma.
        .assign(
            generated_sql=lambda x: sql_generation_chain.invoke({"question": x["standalone_question"]})
        )
        # Passo 3: Executa a query e atualiza o estado da sessão (sem mudanças aqui).
        .assign(
            query_result=execute_and_log_query,
            _update_sql=lambda x, config: update_last_sql(config["configurable"]["session_id"], x["generated_sql"])
        )
        # Passo 4: Gera a resposta final, também usando a pergunta autônoma para contexto.
        .assign(
            final_response_json=lambda x: final_response_chain.invoke({
                "question": x["standalone_question"],
                "query_result": x["query_result"]
            })
        )
        # Passo 5: Combina a resposta com o SQL gerado (sem mudanças aqui).
        | RunnableLambda(combine_sql_with_response)
    )

    # Cadeia de fallback para quando a pergunta não se encaixa em nenhuma categoria
    fallback_chain = RunnableLambda(lambda x: {"type": "text", "content": "Desculpe, não entendi sua pergunta. Pode reformular?"})

    # A lógica de roteamento principal, que direciona para a cadeia correta
    branch = RunnableBranch(
        # Se a intenção for 'consulta_ao_banco_de_dados', usa a nova sql_chain com rephraser
        (lambda x: "consulta_ao_banco_de_dados" in x["topic"], sql_chain),
        # Se for 'saudacao_ou_conversa_simples', usa a cadeia de chat simples
        (lambda x: "saudacao_ou_conversa_simples" in x["topic"], simple_chat_chain),
        # Caso contrário, usa a cadeia de fallback
        fallback_chain,
    )

    def format_final_output(chain_output: dict) -> dict:
        """
        Formata a saída final da cadeia para ser consumida pela API e pelo histórico.
        """
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