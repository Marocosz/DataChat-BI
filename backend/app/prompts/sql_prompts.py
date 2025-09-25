# =================================================================================================
# =================================================================================================
#
#                 ARQUIVO DE PROMPTS - O CÉREBRO CONVERSACIONAL DA APLICAÇÃO
#
# Visão Geral da Arquitetura de Prompts:
#
# Este arquivo define o comportamento da inteligência artificial através de uma série de "prompts"
# especializados, que funcionam como uma linha de montagem para processar a pergunta do usuário:
#
# 1. ROUTER_PROMPT (O Porteiro):
#    - Classifica a pergunta do usuário para decidir se é uma conversa simples ou uma
#      consulta ao banco de dados, direcionando para o especialista correto.
#
# 2. REPHRASER_PROMPT (O Especialista em Contexto):
#    - Se for uma consulta, este prompt reescreve perguntas ambíguas ou de acompanhamento
#      (ex: "e para ele?") em uma pergunta completa e autônoma, usando o histórico do chat.
#
# 3. SQL_PROMPT (O Engenheiro de Banco de Dados):
#    - Recebe a pergunta já clara do Rephraser e a traduz em uma query SQL precisa,
#      usando exemplos de "Few-Shot Learning" para garantir a sintaxe correta.
#
# 4. FINAL_ANSWER_PROMPT (O Analista de Dados e Comunicador):
#    - Pega o resultado bruto da query SQL e o transforma em uma resposta amigável para o
#      usuário, decidindo entre um texto simples ou um gráfico e formatando a saída em JSON.
#
# Cada prompt é um especialista em sua própria tarefa, tornando o sistema modular e robusto.
#
# =================================================================================================
# =================================================================================================

# Importa as classes necessárias do LangChain para construir os templates de prompt.
# PromptTemplate é usado para prompts simples com variáveis.
# FewShotPromptTemplate é para prompts mais complexos que aprendem com exemplos.
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

# --- Bloco 1: O Engenheiro de Banco de Dados (SQL_PROMPT) ---

# Define uma lista de exemplos de alta qualidade (técnica de "Few-Shot Learning").
# Estes exemplos ensinam o LLM a traduzir perguntas em linguagem natural para o SQL
# específico do nosso banco de dados, cobrindo casos como JOINs, agregações e subqueries.
# Esta lista é o principal fator para a precisão da geração de SQL.
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

# Cria um template para formatar cada um dos exemplos acima em um texto consistente.
EXAMPLE_PROMPT_TEMPLATE = PromptTemplate.from_template(
    "User question: {input}\nSQL query: {query}"
)

# Define as instruções principais para o LLM Gerador de SQL.
# Com a arquitetura do Rephraser, sua tarefa é muito mais simples e direta.
SQL_GENERATION_SYSTEM_PROMPT = """
Você é um assistente especialista em PostgreSQL. Sua única tarefa é gerar uma query SQL com base na pergunta do usuário e no esquema do banco de dados.

- A pergunta que você receberá já estará completa, clara e autônoma. Você NÃO PRECISA se preocupar com o histórico da conversa.
- Sua tarefa é simplesmente traduzir a pergunta para uma query SQL válida.
- A query deve ser sintaticamente correta para PostgreSQL.
- Siga as regras gerais: não inclua explicações ou ```sql``` na saída, apenas o código da query.

**Sua Resposta Final DEVE SER APENAS O CÓDIGO SQL.**
---
Aqui está o esquema do banco de dados: {schema}

Considere os seguintes exemplos de perguntas e queries bem-sucedidas:
"""

# Monta o prompt final para a geração de SQL.
# `prefix`: Contém as instruções principais e o esquema do banco.
# `examples`: A lista de exemplos que o LLM usará para aprender.
# `suffix`: Onde a pergunta final do usuário é inserida.
# `input_variables`: Declara quais variáveis este prompt espera receber.
SQL_PROMPT = FewShotPromptTemplate(
    examples=FEW_SHOT_EXAMPLES,
    example_prompt=EXAMPLE_PROMPT_TEMPLATE,
    prefix=SQL_GENERATION_SYSTEM_PROMPT,
    suffix="User question: {question}\nSQL query:",
    input_variables=["question", "schema"],
    example_separator="\n\n"
)

"""
--- Exemplo de Uso e Saída (SQL_PROMPT) ---

INPUT (O que a cadeia fornece a este prompt):
{
  "question": "Qual o número total de operações para o cliente 'Porto'?",
  "schema": "CREATE TABLE clientes (id INTEGER, nome_razao_social VARCHAR) CREATE TABLE operacoes_logisticas (id INTEGER, cliente_id INTEGER)"
}

SAÍDA GERADA PELO LLM:
SELECT COUNT(o.id) FROM operacoes_logisticas o JOIN clientes c ON o.cliente_id = c.id WHERE c.nome_razao_social = 'Porto';
"""


# --- Bloco 2: O Analista de Dados e Comunicador (FINAL_ANSWER_PROMPT) ---

# Define as instruções para o LLM que formata a resposta final para o usuário.
# Ele recebe o resultado bruto do banco e a pergunta original (já reescrita).
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

"""
--- Exemplo de Uso e Saída (FINAL_ANSWER_PROMPT) ---

INPUT (Exemplo 1 - Texto):
{
  "question": "Quantas operações foram canceladas?",
  "result": "[{'count': 123}]",
  "format_instructions": "The output must be a valid JSON. See above."
}

SAÍDA GERADA PELO LLM (Exemplo 1):
{
    "type": "text",
    "content": "Foram canceladas um total de 123 operações."
}

---

INPUT (Exemplo 2 - Gráfico):
{
  "question": "Qual o valor total de frete para cada estado de destino?",
  "result": "[('SP', 50000.00), ('MG', 30000.00), ('RJ', 25000.00)]",
  "format_instructions": "The output must be a valid JSON. See above."
}

SAÍDA GERADA PELO LLM (Exemplo 2):
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


# --- Bloco 3: O Porteiro (ROUTER_PROMPT) ---

# Define as instruções para o LLM classificador de intenção.
# Sua única função é decidir se a pergunta do usuário é uma conversa casual
# ou se ela precisa ser enviada para a complexa cadeia de consulta ao banco de dados.
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

"""
--- Exemplo de Uso e Saída (ROUTER_PROMPT) ---

INPUT (Exemplo 1):
{
  "question": "Olá, como você está?",
  "chat_history": []
}

SAÍDA GERADA PELO LLM (Exemplo 1):
saudacao_ou_conversa_simples

---

INPUT (Exemplo 2):
{
  "question": "e o total de frete deles?",
  "chat_history": ["user: Liste os 5 maiores clientes.", "assistant: Os 5 maiores clientes são..."]
}

SAÍDA GERADA PELO LLM (Exemplo 2):
consulta_ao_banco_de_dados
"""


# --- Bloco 4: O Especialista em Contexto (REPHRASER_PROMPT) ---

# Define as instruções para o LLM que reescreve a pergunta do usuário.
# Esta é a primeira etapa da cadeia de consulta ao banco. Ele pega uma pergunta
# potencialmente ambígua e o histórico do chat e a transforma em uma pergunta
# completa e autônoma, pronta para ser enviada ao Gerador de SQL.
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

"""
--- Exemplo de Uso e Saída (REPHRASER_PROMPT) ---

INPUT (Exemplo 1 - Pergunta já completa):
{
  "question": "Qual o valor total de frete para o estado de SP?",
  "chat_history": ["user: Olá", "assistant: Olá, como posso ajudar?"]
}

SAÍDA GERADA PELO LLM (Exemplo 1):
Qual o valor total de frete para o estado de SP?

---

INPUT (Exemplo 2 - Pergunta de acompanhamento):
{
  "question": "e quantas operações ele teve?",
  "chat_history": ["user: Qual o cliente com maior valor de mercadorias?", "assistant: O cliente com maior valor é 'Porto'."]
}

SAÍDA GERADA PELO LLM (Exemplo 2):
Qual o número total de operações que o cliente 'Porto' teve?
"""