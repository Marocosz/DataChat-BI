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
# Este bloco contém todos os componentes para a tarefa de transformar a pergunta
# do usuário (em português) em uma query SQL válida para o PostgreSQL.

# "Few-Shot"
# Esta lista é a parte mais CRÍTICA para a precisão do nosso sistema.
# Ela funciona como um "gabarito" que ensina o LLM, através de exemplos,
# como traduzir perguntas para o esquema do banco de dados específico.
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

# Template auxiliar para formatar exemplos
EXAMPLE_PROMPT_TEMPLATE = PromptTemplate.from_template(
    "User question: {input}\nSQL query: {query}"
)

# Prompt principal para geração de SQL
SQL_GENERATION_SYSTEM_PROMPT = """
Você é um assistente especialista em PostgreSQL. Sua principal tarefa é gerar uma única query SQL com base na pergunta do usuário e no contexto fornecido.

Pense passo a passo antes de gerar a query:

**Passo 1: Analise a Pergunta Atual do Usuário.**
- Se a pergunta é completa e não depende do histórico (ex: "Qual o valor total de frete?"), sua tarefa é simplesmente traduzir essa pergunta para SQL. Pule para o Passo 3.
- Se a pergunta é um acompanhamento que usa termos como 'ele', 'dela', 'disso', ou é uma frase incompleta (ex: "e o total de operações?"), ela depende do contexto. Vá para o Passo 2.

**Passo 2: Analise o Contexto da Conversa.**
- Olhe a "Query SQL da Última Pergunta". Ela é a fonte da verdade para o contexto.
- A query anterior identificou uma entidade principal (ex: o cliente 'Porto', encontrado com a lógica `ORDER BY SUM(...)`).
- Sua nova query DEVE filtrar os resultados usando a lógica EXATA da query anterior dentro de uma cláusula `WHERE` com uma subquery.

**Passo 3: Construa a Query Final.**
- Com base na sua análise, construa a query SQL.
- A query deve ser sintaticamente correta para PostgreSQL.
- Siga as regras gerais: não inclua explicações ou ```sql``` na saída, apenas o código da query.

**Sua Resposta Final DEVE SER APENAS O CÓDIGO SQL.**
---
Histórico da Conversa:
{chat_history}
---
Query SQL da Última Pergunta:
```sql
{previous_sql}

Aqui está o esquema do banco de dados: {schema}

Considere os seguintes exemplos de perguntas e queries bem-sucedidas:
"""

# Construtor do prompt final de SQL
SQL_PROMPT = FewShotPromptTemplate(
    examples=FEW_SHOT_EXAMPLES,
    example_prompt=EXAMPLE_PROMPT_TEMPLATE,
    prefix=SQL_GENERATION_SYSTEM_PROMPT,
    suffix="User question: {question}\nSQL query:",
    input_variables=["question", "schema", "chat_history", "previous_sql"],
    example_separator="\n\n"
)

# --- Exemplo de Saída do Bloco 1 ---
"""
INPUT:
question = "Quantas operações foram canceladas no último mês?"
schema = "CREATE TABLE operacoes_logisticas (id SERIAL, status VARCHAR, data_emissao DATE);"
chat_history = "Histórico da conversa: user: Qual o total de operações? assistant: O total de operações é 1500."
previous_sql = "SELECT COUNT(*) FROM operacoes_logisticas;"

SAÍDA GERADA PELO PROMPT:
SELECT COUNT(*) FROM operacoes_logisticas WHERE status = 'CANCELADO' AND data_emissao >= '2023-08-01' AND data_emissao <= '2023-08-31';
"""


# --- Bloco 2: Geração da Resposta Final (Analista de Dados) ---
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

# --- Exemplo de Saída do Bloco 2 ---
"""
INPUT:
question = "Quantas operações foram canceladas?"
result = "[('count', 123)]"
format_instructions = "The output must be a valid JSON. See above."

SAÍDA GERADA PELO PROMPT:
{
    "type": "text",
    "content": "Houve 123 operações canceladas."
}
"""

"""
INPUT:
question = "Qual o valor total de frete para cada estado de destino?"
result = "[('SP', 50000.00), ('MG', 30000.00), ('RJ', 25000.00)]"
format_instructions = "The output must be a valid JSON. See above."

SAÍDA GERADA PELO PROMPT:
{
    "type": "chart",
    "chart_type": "bar",
    "title": "Valor Total de Frete por Estado de Destino",
    "data": [{"uf_destino": "SP", "valor_total_frete": 50000.00}, {"uf_destino": "MG", "valor_total_frete": 30000.00}, {"uf_destino": "RJ", "valor_total_frete": 25000.00}],
    "x_axis": "uf_destino",
    "y_axis": ["valor_total_frete"],
    "y_axis_label": "Valor Total Frete (R$)"
}
"""


# --- Bloco 3: Roteador de Intenção ---
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

# --- Exemplo de Saída do Bloco 3 ---
"""
INPUT:
question = "Olá, como você está?"
chat_history = ""

SAÍDA GERADA PELO PROMPT:
saudacao_ou_conversa_simples
"""

"""
INPUT:
question = "Quantas operações foram concluídas?"
chat_history = "Histórico: N/A"

SAÍDA GERADA PELO PROMPT:
consulta_ao_banco_de_dados
"""