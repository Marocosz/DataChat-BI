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
# Ela funciona como um "gabarito" ou "cola" que ensina o LLM, através de exemplos,
# como ele deve traduzir perguntas para o nosso esquema de banco de dados específico.
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

# Template para Formatar os Exemplos
# Este é um pequeno template auxiliar que define como cada exemplo da lista acima
# será formatado antes de ser inserido no prompt final.
EXAMPLE_PROMPT_TEMPLATE = PromptTemplate.from_template(
    "User question: {input}\nSQL query: {query}"
)

# O Manual de Instruções para o Gerador de SQL
# Este é o prompt de sistema (as instruções principais) para o LLM.
# Ele define o "personagem" (especialista em PostgreSQL) e as regras que ele deve seguir.
SQL_GENERATION_SYSTEM_PROMPT = """
Você é um assistente especialista em PostgreSQL. Sua única função é analisar a pergunta de um usuário e o esquema de um banco de dados para gerar uma query SQL sintaticamente correta.

**Regras Importantes:**
- Apenas gere a query SQL.
- Não inclua ```sql, ``` ou qualquer outra explicação ou texto antes ou depois da query.
- Use as tabelas e colunas do esquema fornecido.
- Para colunas com valores pré-definidos (como 'status' e 'tipo'), você DEVE usar um dos valores exatos fornecidos na descrição da coluna no schema.
- Se a pergunta envolver datas, use a data atual como `NOW()` quando apropriado.
- **REGRA DE OURO:** A menos que a pergunta peça explicitamente por uma agregação total (como COUNT(*), SUM(coluna), AVG(coluna) sem um GROUP BY), **SEMPRE adicione uma cláusula `LIMIT` à sua query para evitar retornar dados demais.** Um bom limite padrão é 50. Se o usuário pedir um número específico (ex: "os 10 maiores"), use esse número.

Considere o histórico da conversa abaixo para entender o contexto da pergunta atual.
---
Histórico da Conversa:
{chat_history}
---

Aqui está o esquema do banco de dados:
{schema}

Considere os seguintes exemplos de perguntas e queries bem-sucedidas:
"""

# O Construtor do Prompt Final de SQL
# O FewShotPromptTemplate é o componente que junta tudo de forma inteligente.
# Ele pega as instruções (prefix), os exemplos formatados (examples), o esquema do banco (schema)
# e a pergunta do usuário (question) para montar dinamicamente um prompt completo e rico em contexto.
SQL_PROMPT = FewShotPromptTemplate(
    examples=FEW_SHOT_EXAMPLES,
    example_prompt=EXAMPLE_PROMPT_TEMPLATE,
    prefix=SQL_GENERATION_SYSTEM_PROMPT,
    suffix="User question: {question}\nSQL query:",
    input_variables=["question", "schema", "chat_history"],
    example_separator="\n\n"
)
"""
(====================== INÍCIO DO PREFIXO ======================)
Você é um assistente especialista em PostgreSQL. Sua única função é analisar a pergunta de um usuário e o esquema de um banco de dados para gerar uma query SQL sintaticamente correta.

**Regras Importantes:**
- Apenas gere a query SQL.
- Não inclua ```sql, ``` ou qualquer outra explicação ou texto antes ou depois da query.
- Use as tabelas e colunas do esquema fornecido.
- Se a pergunta envolver datas, use a data atual como `NOW()` quando apropriado.
- **REGRA DE OURO:** A menos que a pergunta peça explicitamente por uma agregação total (como COUNT(*), SUM(coluna), AVG(coluna) sem um GROUP BY), **SEMPRE adicione uma cláusula `LIMIT` à sua query para evitar retornar dados demais.** Um bom limite padrão é 50. Se o usuário pedir um número específico (ex: "os 10 maiores"), use esse número.

Considere o histórico da conversa abaixo para entender o contexto da pergunta atual.
---
Histórico da Conversa:

---

Aqui está o esquema do banco de dados:
Tabela: clientes
Colunas: id (integer), nome_razao_social (character varying), cnpj_cpf (character varying), email_contato (character varying), telefone_contato (character varying), data_cadastro (timestamp with time zone)

Tabela: operacoes_logisticas
Colunas: id (bigint), codigo_operacao (character varying), tipo (tipo_operacao_logistica), status (status_operacao), cliente_id (integer), data_emissao (timestamp with time zone), data_previsao_entrega (date), data_entrega_realizada (timestamp with time zone), uf_coleta (character varying), cidade_coleta (character varying), uf_destino (character varying), cidade_destino (character varying), peso_kg (numeric), quantidade_volumes (integer), valor_mercadoria (numeric), natureza_carga (character varying), valor_frete (numeric), valor_seguro (numeric), codigo_rastreio (character varying), observacoes (text)

Considere os seguintes exemplos de perguntas e queries bem-sucedidas:
(======================= FIM DO PREFIXO ========================)

(====================== INÍCIO DO RECHEIO ======================)
User question: Quantas operações de transporte estão 'EM_TRANSITO'?
SQL query: SELECT count(*) FROM operacoes_logisticas WHERE tipo = 'TRANSPORTE' AND status = 'EM_TRANSITO';

User question: Liste os nomes dos clientes que tiveram operações com valor de mercadoria acima de 10.000.
SQL query: SELECT c.nome_razao_social FROM clientes c JOIN operacoes_logisticas o ON c.id = o.cliente_id WHERE o.valor_mercadoria > 10000;

User question: Qual o valor total de frete agrupado por estado de destino (uf_destino)? Apresente os 5 maiores.
SQL query: SELECT uf_destino, SUM(valor_frete) AS valor_total_frete FROM operacoes_logisticas GROUP BY uf_destino ORDER BY valor_total_frete DESC LIMIT 5;

User question: Qual o prazo médio de entrega para operações já concluídas?
SQL query: SELECT AVG(data_entrega_realizada - data_emissao) AS prazo_medio FROM operacoes_logisticas WHERE status = 'ENTREGUE';
(======================== FIM DO RECHEIO =======================)

(======================= INÍCIO DO SUFIXO =======================)
User question: Qual cliente teve o maior número de operações canceladas?
SQL query:
(======================== FIM DO SUFIXO ========================)
"""

# --- Bloco 2: Geração da Resposta Final (Analista de Dados) ---
# Este prompt transforma o resultado bruto do banco de dados em uma resposta
# estruturada e amigável, decidindo se deve apresentar texto ou um gráfico.
FINAL_ANSWER_PROMPT = PromptTemplate.from_template(
    """
    Sua tarefa é atuar como um analista de dados especialista e assistente de comunicação.
    Dada a pergunta original do usuário e o resultado de uma consulta ao banco de dados, formule a melhor resposta possível em português.

    **REGRAS DE FORMATAÇÃO DA SAÍDA:**
    1.  **SE** o resultado dos dados for apropriado para uma visualização (ex: dados agrupados, séries temporais, comparações), sua resposta **DEVE** ser um JSON bem-formado que descreve o gráfico.
    2.  **SE** o resultado for um único valor, uma lista simples, ou texto, sua resposta **DEVE** ser um JSON com um campo de texto.
    3.  Nunca responda com texto puro. A saída deve ser sempre um JSON válido.
    4.  **SE** o usuário especificar um tipo de gráfico (ex: 'gráfico de linha', 'pizza', 'barras'), sua resposta **DEVE** usar esse `chart_type`. Se não, escolha o mais apropriado.

    ---
    **ESPECIFICAÇÃO DO JSON PARA GRÁFICOS:**
    ```json
    {{
      "type": "chart",
      "chart_type": "bar | line | pie",
      "title": "Um título descritivo para o gráfico",
      "data": [{{ "campo1": "valor1", "campo2": 10 }}, {{ "campo1": "valor2", "campo2": 20 }}],
      "x_axis": "nome_da_chave_para_o_eixo_x",
      "y_axis": ["nome_da_chave_para_o_eixo_y"],
      "y_axis_label": "Um nome descritivo para o valor do eixo Y (ex: 'Valor do Frete (R$)')"
    }}
    ```

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
        **Resultado do BD:** `[{{'uf_destino': 'SP', 'valor_total_frete': 15000.00}}, {{'uf_destino': 'MG', 'valor_total_frete': 8000.00}}]`
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
            "y_axis": ["valor_total_frete"],
            "y_axis_label": "Valor Total do Frete"
        }}
        ```
    * **Pergunta:** "Qual o status da operação 'OP-12345'?"
        **Resultado do BD:** `[{{'status': 'EM_TRANSITO'}}]`
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
    
    {format_instructions}

    **Sua Resposta (APENAS O JSON):**
    """
)

# --- Bloco 3: Roteador de Intenção ---
# Este prompt é para uma tarefa rápida e barata de classificação. Ele atua como o
# "porteiro" ou "sistema de triagem" da aplicação, decidindo se a pergunta do usuário
# precisa ir para a complexa cadeia de banco de dados ou para uma simples resposta de saudação.
ROUTER_PROMPT = PromptTemplate.from_template(
    """
    Sua tarefa é classificar o texto do usuário em uma das duas categorias a seguir, com base em sua intenção. Responda APENAS com o nome da categoria, e nada mais.
    Primeiro, analise o histórico da conversa para obter contexto sobre a pergunta atual.

    ---
    Histórico da Conversa:
    {chat_history}
    ---

    CATEGORIAS:
    - `consulta_ao_banco_de_dados`: Se a pergunta parece ser uma solicitação de dados, insights, relatórios, listas ou informações específicas sobre operações, clientes, fretes, etc. (incluindo perguntas de acompanhamento como "e o valor dele?").
    - `saudacao_ou_conversa_simples`: Se a pergunta é uma saudação, despedida, agradecimento ou qualquer outra forma de conversa que não busca dados específicos.

    Texto do usuário:
    {question}

    Categoria:
    """
)