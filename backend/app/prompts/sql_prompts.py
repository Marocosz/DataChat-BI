# =============================================================================
# ARQUIVO DE PROMPTS - O CÉREBRO CONVERSACIONAL DA APLICAÇÃO "prompt engineering".
#
# Este arquivo centraliza todas as instruções (prompts) que guiam o
# comportamento dos modelos de linguagem (LLMs). Cada variável aqui define uma
# tarefa específica, como gerar SQL, classificar a intenção do usuário ou
# formatar a resposta final.
# =============================================================================

from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

# --- Bloco 1: Geração de SQL ---
# Este bloco contém todos os componentes para a tarefa de transformar a pergunta
# do usuário (em português) em uma query SQL válida para o PostgreSQL.

# "Few-Shot"
# Esta lista é a parte mais CRÍTICA para a precisão do nosso sistema.
# Ela funciona como um "gabarito" que ensina o LLM, através de exemplos,
# como traduzir perguntas para o esquema do banco de dados específico.
FEW_SHOT_EXAMPLES = [
    # -------------------------------------------------------------------------
    # Exemplos Originais
    # -------------------------------------------------------------------------
    {
        "input": "Quantas operações foram canceladas?",
        "query": "SELECT count(*) FROM operacoes_logisticas WHERE status = 'CANCELADO';"
    },
    {
        "input": "Quantas operações de transporte estão 'EM_TRANSITO'?",
        "query": "SELECT count(*) FROM operacoes_logisticas WHERE tipo = 'TRANSPORTE' AND status = 'EM_TRANSITO';"
    },
    {
        "input": "Liste os nomes dos clientes que tiveram operações com valor de mercadoria acima de 10.000.",
        "query": "SELECT c.nome_razao_social FROM clientes c JOIN operacoes_logisticas o ON c.id = o.cliente_id WHERE o.valor_mercadoria > 10000;"
    },
    {
        "input": "Qual o valor total de frete agrupado por estado de destino (uf_destino)? Apresente os 5 maiores.",
        "query": "SELECT uf_destino, SUM(valor_frete) AS valor_total_frete FROM operacoes_logisticas GROUP BY uf_destino ORDER BY valor_total_frete DESC LIMIT 5;"
    },
    {
        "input": "Qual o prazo médio de entrega para operações já concluídas?",
        "query": "SELECT AVG(data_entrega_realizada - data_emissao) AS prazo_medio FROM operacoes_logisticas WHERE status = 'ENTREGUE';"
    },

    # -------------------------------------------------------------------------
    # Novos exemplos: Perguntas de acompanhamento (contexto)
    # -------------------------------------------------------------------------

    # --- CENÁRIO 1: Lógica baseada em SOMA (SUM) ---
    {
        # Pergunta 1: Estabelece um contexto (o cliente com maior valor).
        "input": "Qual o cliente com maior valor total de mercadorias?",
        "query": "SELECT c.nome_razao_social, SUM(o.valor_mercadoria) as total_valor FROM clientes c JOIN operacoes_logisticas o ON c.id = o.cliente_id GROUP BY c.nome_razao_social ORDER BY total_valor DESC LIMIT 1;"
    },
    {
        "input": "e quantas operações ele teve no total?",
        "query": """SELECT COUNT(o.id) 
FROM operacoes_logisticas o 
JOIN clientes c ON o.cliente_id = c.id 
WHERE c.nome_razao_social = (
    SELECT c.nome_razao_social 
    FROM clientes c 
    JOIN operacoes_logisticas o ON c.id = o.cliente_id 
    GROUP BY c.nome_razao_social 
    ORDER BY SUM(o.valor_mercadoria) DESC 
    LIMIT 1
);"""
    },

    # --- Cenário 2: Lógica baseada em COUNT + WHERE ---
    {
        "input": "Qual cliente teve o maior número de operações canceladas?",
        "query": """SELECT c.nome_razao_social 
FROM clientes c 
JOIN operacoes_logisticas o ON c.id = o.cliente_id 
WHERE o.status = 'CANCELADO' 
GROUP BY c.nome_razao_social 
ORDER BY COUNT(o.id) DESC 
LIMIT 1;"""
    },
    {
        "input": "e qual o valor médio de mercadoria dele?",
        "query": """SELECT AVG(o.valor_mercadoria) 
FROM operacoes_logisticas o 
JOIN clientes c ON o.cliente_id = c.id 
WHERE c.nome_razao_social = (
    SELECT c.nome_razao_social 
    FROM clientes c 
    JOIN operacoes_logisticas o ON c.id = o.cliente_id 
    WHERE o.status = 'CANCELADO' 
    GROUP BY c.nome_razao_social 
    ORDER BY COUNT(o.id) DESC 
    LIMIT 1
);"""
    }
]

# Template auxiliar para formatar exemplos
EXAMPLE_PROMPT_TEMPLATE = PromptTemplate.from_template(
    "User question: {input}\nSQL query: {query}"
)

# Prompt principal para geração de SQL
SQL_GENERATION_SYSTEM_PROMPT = """
Você é um assistente especialista em PostgreSQL. Sua única função é analisar a pergunta de um usuário e o esquema de um banco de dados para gerar uma query SQL sintaticamente correta.

**Regras Importantes:**
- Apenas gere a query SQL.
- Não inclua ```sql, ``` ou qualquer outra explicação ou texto antes ou depois da query.
- Use as tabelas e colunas do esquema fornecido.
- Para colunas com valores pré-definidos (como 'status' e 'tipo'), você DEVE usar os valores exatos fornecidos.
- Se a pergunta envolver datas, use a data atual como `NOW()` quando apropriado.
- **Regra de Ouro:** A menos que a pergunta peça explicitamente por uma agregação total (COUNT, SUM, AVG sem GROUP BY), **sempre adicione `LIMIT`** para evitar excesso de dados. Padrão = 50. Se o usuário pedir um número específico, use-o.

---
**Contexto da Conversa:**
- Perguntas podem ser continuação da anterior. **Preste atenção ao histórico.**
- Resolva pronomes (ele, dela, isso, último) com base na **entidade principal da pergunta anterior**.
- Se a pergunta anterior envolveu lógica complexa para encontrar uma entidade (ex: maior faturamento), a atual **deve reutilizar a mesma lógica** em subquery ou WHERE. **Não altere a lógica de seleção do contexto.**
---

Histórico da Conversa:
{chat_history}

A query SQL gerada para a última pergunta foi:
{previous_sql}

Aqui está o esquema do banco de dados:
{schema}

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
