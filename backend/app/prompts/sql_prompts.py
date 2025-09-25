# ================================================================================================================
# ARQUIVO DE PROMPTS - O CÉREBRO CONVERSACIONAL DA APLICAÇÃO "prompt engineering".
#
# Este arquivo centraliza todas as instruções (prompts) que guiam o
# comportamento dos modelos de linguagem (LLMs). Cada variável aqui define uma
# tarefa específica, como gerar SQL, classificar a intenção do usuário ou
# formatar a resposta final.
# ================================================================================================================

from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

# --- Bloco 1: Geração de SQL ---
# ATUALIZAÇÃO: Este bloco foi simplificado para funcionar com a nova arquitetura do "Rephraser".
# Ele não lida mais com o histórico da conversa, recebendo sempre uma pergunta completa.

# "Few-Shot": A lista de exemplos permanece a mesma, pois continua sendo valiosa.
FEW_SHOT_EXAMPLES = [
    {
        "input": "Quantas operações foram canceladas?",
        "query": "SELECT count(*) FROM operacoes_logisticas WHERE status = 'CANCELADO';"
    },
    {
        "input": "Quantas operações de transporte estão 'EM_TRANSITO'?",
        "query": "SELECT count(*) FROM operacoes_logisticas WHERE tipo = 'TRANSPORTE' AND status = 'EM_TRANSITO';"
    },
    {
        "input": "Liste os nomes dos 5 clientes com operações de valor acima de 10.000.",
        "query": "SELECT c.nome_razao_social FROM clientes c JOIN operacoes_logisticas o ON c.id = o.cliente_id WHERE o.valor_mercadoria > 10000 LIMIT 5;"
    },
    {
        "input": "Qual o valor total de frete para cada estado de destino? Mostre os 5 maiores.",
        "query": "SELECT uf_destino, SUM(valor_frete) AS valor_total_frete FROM operacoes_logisticas GROUP BY uf_destino ORDER BY valor_total_frete DESC LIMIT 5;"
    },
    {
        "input": "Qual o prazo médio de entrega para operações já concluídas?",
        "query": "SELECT AVG(data_entrega_realizada - data_emissao) AS prazo_medio FROM operacoes_logisticas WHERE status = 'ENTREGUE';"
    },
    {
        "input": "Qual o cliente com maior valor total de mercadorias?",
        "query": "SELECT c.nome_razao_social, SUM(o.valor_mercadoria) as total_valor FROM clientes c JOIN operacoes_logisticas o ON c.id = o.cliente_id GROUP BY c.nome_razao_social ORDER BY total_valor DESC LIMIT 1;"
    },
    {
        "input": "Quantos clientes possuem 100 ou mais operações com status EM_TRANSITO para o estado de SP?",
        "query": """WITH clientes_filtrados AS (SELECT o.cliente_id FROM operacoes_logisticas o WHERE o.uf_destino = 'SP' AND o.status = 'EM_TRANSITO' GROUP BY o.cliente_id HAVING COUNT(o.id) >= 100) SELECT COUNT(*) AS total_clientes FROM clientes_filtrados;"""
    }
]

# Template auxiliar para formatar exemplos (sem alteração)
EXAMPLE_PROMPT_TEMPLATE = PromptTemplate.from_template(
    "User question: {input}\nSQL query: {query}"
)

# ATUALIZAÇÃO: O prompt principal para geração de SQL agora é muito mais simples.
SQL_GENERATION_SYSTEM_PROMPT = """
Você é um assistente especialista em PostgreSQL. Sua única tarefa é gerar uma query SQL com base na pergunta do usuário e no esquema do banco de dados.

- A pergunta que você receberá já estará completa, clara e autônoma. Você NÃO PRECISA se preocupar com o histórico da conversa.
- Sua tarefa é simplesmente traduzir a pergunta para uma query SQL válida.
- A query deve ser sintaticamente correta для PostgreSQL.
- Siga as regras gerais: não inclua explicações ou ```sql``` na saída, apenas o código da query.

**Sua Resposta Final DEVE SER APENAS O CÓDIGO SQL.**
---
Aqui está o esquema do banco de dados: {schema}

Considere os seguintes exemplos de perguntas e queries bem-sucedidas:
"""

# ATUALIZAÇÃO: O construtor do prompt agora aponta para o novo System Prompt
# e, o mais importante, declara que só espera as variáveis `question` e `schema`.
SQL_PROMPT = FewShotPromptTemplate(
    examples=FEW_SHOT_EXAMPLES,
    example_prompt=EXAMPLE_PROMPT_TEMPLATE,
    prefix=SQL_GENERATION_SYSTEM_PROMPT,
    suffix="User question: {question}\nSQL query:",
    input_variables=["question", "schema"],
    example_separator="\n\n"
)


# --- Bloco 2: Geração da Resposta Final (Analista de Dados) ---
# Nenhuma alteração necessária neste bloco.
FINAL_ANSWER_PROMPT = PromptTemplate.from_template(
    """
    Sua tarefa é atuar como analista de dados e assistente de comunicação.
    Dada a pergunta original do usuário e o resultado da consulta ao banco, formule a melhor resposta possível em português.

    **Regras de Formatação da Saída:**
    1. Se for apropriado para gráfico (dados agrupados, séries, comparações), responda em JSON de gráfico.
    2. Se for valor único, lista simples ou texto, responda em JSON de texto.
    3. Nunca responda em texto puro. Sempre JSON válido.
    4. Se o usuário pedir um tipo de gráfico, use-o. Senão, escolha o mais apropriado.
    5. Se o 'Resultado do Banco de Dados' for `RESULTADO_VAZIO: ...`, sua resposta deve ser um JSON de texto informando que os dados não foram encontrados. Nunca invente uma resposta.

    ---
    **Formato JSON para gráficos:**
    {{
      "type": "chart",
      "chart_type": "bar | line | pie",
      "title": "Título do gráfico",
      "data": [{{"campo1": "valor1", "campo2": 10}}, {{"campo1": "valor2", "campo2": 20}}],
      "x_axis": "campo eixo X",
      "y_axis": ["campo eixo Y"],
      "y_axis_label": "Descrição eixo Y"
    }}

    **Formato JSON para texto:**
    {{
      "type": "text",
      "content": "Resposta em texto claro aqui."
    }}
    ---

    Pergunta Original: {question}
    Resultado do Banco de Dados:
    {result}

    {format_instructions}

    **Sua Resposta (apenas JSON):**
    """
)


# --- Bloco 3: Roteador de Intenção ---
# Nenhuma alteração necessária neste bloco.
ROUTER_PROMPT = PromptTemplate.from_template(
    """
    Sua tarefa é classificar o texto do usuário em uma das duas categorias. Responda APENAS com o nome da categoria.

    ---
    Histórico da Conversa:
    {chat_history}
    ---

    Categorias:
    - `consulta_ao_banco_de_dados`: Solicitações de dados, relatórios, listas, informações específicas (inclui perguntas de acompanhamento).
    - `saudacao_ou_conversa_simples`: Saudações, despedidas, agradecimentos ou conversa sem dados.

    Texto do usuário:
    {question}

    Categoria:
    """
)


# --- Bloco 4: Reescrever a Pergunta com Contexto (REPHRASER) ---
# Este é o novo prompt que você adicionou, está perfeito.
REPHRASER_PROMPT = PromptTemplate.from_template(
    """
    Sua única tarefa é reescrever a pergunta do usuário para que ela seja autônoma, usando o histórico da conversa como contexto.
    - Se a pergunta do usuário já for completa e não precisar de contexto, apenas a retorne como está.
    - Se a pergunta for um acompanhamento (usando 'ele', 'disso', 'e para lá?'), use as mensagens anteriores para completá-la.
    - Seja conciso e direto na pergunta reescrita.

    ---
    Histórico da Conversa:
    {chat_history}
    ---

    Pergunta do Usuário: {question}
    Pergunta Reescrita:
    """
)