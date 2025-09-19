# app/prompts/sql_prompts.py
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.prompts import PromptTemplate

# 1. Definição dos Exemplos (Few-Shot Examples)
# A qualidade destes exemplos define a performance do seu sistema.
FEW_SHOT_EXAMPLES = [
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
    }
]

# 2. Template para formatar cada exemplo
EXAMPLE_PROMPT_TEMPLATE = PromptTemplate.from_template(
    "User question: {input}\nSQL query: {query}"
)

# 3. Template Principal (System Prompt) que guia o LLM
SQL_GENERATION_SYSTEM_PROMPT = """
Você é um assistente especialista em PostgreSQL. Sua única função é analisar a pergunta de um usuário e o esquema de um banco de dados para gerar uma query SQL sintaticamente correta.

**Regras Importantes:**
- Apenas gere a query SQL.
- Não inclua ```sql, ``` ou qualquer outra explicação ou texto antes ou depois da query.
- Use as tabelas e colunas do esquema fornecido.
- Se a pergunta envolver datas, use a data atual como `NOW()` quando apropriado.

Aqui está o esquema do banco de dados:
{schema}

Considere os seguintes exemplos de perguntas e queries bem-sucedidas:
{examples}
"""

# 4. Construção do FewShotPromptTemplate
SQL_PROMPT = FewShotPromptTemplate(
    examples=FEW_SHOT_EXAMPLES,
    example_prompt=EXAMPLE_PROMPT_TEMPLATE,
    prefix=SQL_GENERATION_SYSTEM_PROMPT,
    suffix="User question: {question}\nSQL query:",
    input_variables=["question", "schema"],
    example_separator="\n\n"
)


# 5. Prompt para a Geração da Resposta Final
FINAL_ANSWER_PROMPT = PromptTemplate.from_template(
    """
    Dada a pergunta original do usuário e o resultado obtido de uma consulta ao banco de dados, sua tarefa é formular uma resposta clara, amigável e concisa em português.

    **Instruções:**
    - Se o resultado for uma lista de dados (uma tabela), formate-a de maneira legível usando Markdown.
    - Se o resultado for um único valor (ex: uma contagem ou uma média), apresente-o em uma frase completa e informativa.
    - Se o resultado indicar um erro, informe ao usuário que não foi possível encontrar a informação e que ele pode tentar reformular a pergunta.
    - Aja como um assistente prestativo. Não mencione que você executou uma query SQL ou mostre o resultado bruto. Apenas apresente o insight final.

    **Pergunta Original:** {question}
    **Resultado do Banco de Dados:**
    {result}

    **Sua Resposta:**
    """
)

FINAL_ANSWER_PROMPT = PromptTemplate.from_template(
    """
    Sua tarefa é atuar como um analista de dados especialista e assistente de comunicação.
    Dada a pergunta original do usuário e o resultado de uma consulta ao banco de dados, formule a melhor resposta possível em português.

    **REGRAS DE FORMATAÇÃO DA SAÍDA:**
    1.  **SE** o resultado dos dados for apropriado para uma visualização (ex: dados agrupados, séries temporais, comparações), sua resposta **DEVE** ser um JSON bem-formado que descreve o gráfico.
    2.  **SE** o resultado for um único valor, uma lista simples, ou texto, sua resposta **DEVE** ser um JSON com um campo de texto.
    3.  Nunca responda com texto puro. A saída deve ser sempre um JSON válido.

    ---
    **ESPECIFICAÇÃO DO JSON PARA GRÁFICOS:**
    ```json
    {{
      "type": "chart",
      "chart_type": "bar | line | pie",
      "title": "Um título descritivo para o gráfico",
      "data": [{{ "campo1": "valor1", "campo2": 10 }}, {{ "campo1": "valor2", "campo2": 20 }}],
      "x_axis": "nome_da_chave_para_o_eixo_x",
      "y_axis": ["nome_da_chave_para_o_eixo_y"]
    }}
    ```
    - `x_axis`: A chave do dicionário de dados que representa a categoria (eixo X).
    - `y_axis`: Uma lista com a(s) chave(s) do dicionário de dados que representa(m) o(s) valor(es) numérico(s) (eixo Y).

    **ESPECIFICAÇÃO DO JSON PARA TEXTO:**
    ```json
    {{
      "type": "text",
      "content": "Sua resposta em texto claro e amigável aqui."
    }}
    ```
    ---

    **EXEMPLOS DE DECISÃO:**

    * **Pergunta:** "Qual o valor total de frete por estado?"
        **Resultado do BD:** `[{'uf_destino': 'SP', 'valor_total_frete': 15000.00}, {'uf_destino': 'MG', 'valor_total_frete': 8000.00}]`
        **SUA RESPOSTA JSON (CORRETA):**
        ```json
        {{
            "type": "chart",
            "chart_type": "bar",
            "title": "Valor Total de Frete por Estado",
            "data": [
                {{ "uf_destino": "SP", "valor_total_frete": 15000.00 }},
                {{ "uf_destino": "MG", "valor_total_frete": 8000.00 }}
            ],
            "x_axis": "uf_destino",
            "y_axis": ["valor_total_frete"]
        }}
        ```
    * **Pergunta:** "Qual o status da operação 'OP-12345'?"
        **Resultado do BD:** `[{'status': 'EM_TRANSITO'}]`
        **SUA RESPOSTA JSON (CORRETA):**
        ```json
        {{
            "type": "text",
            "content": "A operação de código OP-12345 está com o status: EM_TRANSITO."
        }}
        ```
    ---
    
    **AGORA, CRIE A RESPOSTA PARA A SEGUINTE SOLICITAÇÃO:**

    **Pergunta Original:** {question}
    **Resultado do Banco de Dados:**
    {result}

    **Sua Resposta (APENAS O JSON):**
    """
)