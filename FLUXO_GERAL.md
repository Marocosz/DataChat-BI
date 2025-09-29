
# DOCUMENTO MESTRE DE ARQUITETURA E FLUXO DE DADOS - SUPPBOT BI

Propósito do Arquivo:
Este documento é a fonte definitiva da verdade sobre o funcionamento interno da
aplicação. Ele descreve a sequência cronológica completa de uma requisição,
desde o clique do usuário no frontend até a resposta da IA, detalhando cada
função, cadeia e componente no momento exato em que ele é acionado no fluxo.

---
## Passo 0: A Preparação (O que acontece UMA VEZ na inicialização do backend)
---
1.  **Comando de Início:** Você executa `uvicorn api:app --reload` no terminal.
2.  **Carregamento da API:** O servidor Uvicorn carrega o arquivo `backend/api.py`.
3.  **CONSTRUÇÃO DA CHAIN:** A linha `rag_chain = create_master_chain()` é executada.
    - **Onde:** `api.py`.
    - **Ação:** A função `create_master_chain()` do arquivo `sql_rag_chain.py` é chamada.
      Ela constrói e conecta TODAS as sub-cadeias e as envolve no `RunnableWithMessageHistory`.
    - **Resultado:** O objeto `rag_chain` (que é o `chain_with_memory`) é criado e armazenado
      na memória. Ele fica pronto, esperando por requisições.

    > **É DAQUI QUE A "CHAIN" É PEGA:** ela é pré-construída e reutilizada para todas as chamadas. Vamos detalhar o objeto principal que é criado:

    
    **Componente Detalhado: `chain_with_memory`**

    - **Propósito:** A cadeia final exportada pelo módulo. Ela envolve a `main_chain` com a lógica de gerenciamento automático de memória, atuando como a porta de entrada de toda a aplicação.
    - **Fluxo Detalhado:**
        1. **Entrada:** Recebe a pergunta do usuário e o `session_id` no objeto `config`.
        2. **Carregar Memória:** Usa a função `get_session_history` para carregar o histórico da conversa para a `session_id` fornecida.
        3. **Invocar a `main_chain`:** Executa a cadeia principal com a pergunta e o histórico carregado.
        4. **Salvar Memória:** Pega a `question` de entrada e a `history_message` de saída e as salva de volta no `store` para a `session_id` correspondente.
    - **Exemplo de Entrada (como a API a chama):**
      - Input: `{"question": "e qual o total de mercadorias dele?"}`
      - Config: `{"configurable": {"session_id": "sessao-456"}}`
    - **Exemplo de Saída (o que a API recebe):**
      - O mesmo dicionário da `main_chain`.
      ```json
      {
          "api_response": { "..."},
          "history_message": "..."
      }
      ```
    

---
## Passo 1: A Pergunta do Usuário (Frontend)
---
1.  **Ação do Usuário:** O usuário digita uma pergunta (ex: "e o total de operações dele?") e clica em "Enviar" na interface.
2.  **Origem:** `frontend/src/pages/Chat.js`.
3.  **Ação do Código:**
    - A função `handleSubmit` é acionada.
    - Ela pega o texto do `input` e o `sessionId` que está guardado no estado do React.
    - A biblioteca `axios` faz uma requisição `HTTP POST` para o endpoint `http://localhost:8000/chat`, enviando um JSON com a `question` e o `session_id`.

---
## Passo 2: A Chegada no Backend (API)
---
1.  **Ação do Servidor:** O FastAPI recebe a requisição POST.
2.  **Origem:** `backend/api.py`.
3.  **Ação do Código:**
    - O FastAPI direciona a requisição para a função `@app.post("/chat") async def chat_endpoint(...)`.
    - O Pydantic valida o JSON recebido e o converte no objeto `request: ChatRequest`.

---
## Passo 3: A Magia da Memória (Invocando a Cadeia)
---
1.  **Ação do Código:** A linha `rag_chain.invoke(...)` é chamada dentro do `chat_endpoint`.
2.  **Lógica Principal:** A execução é entregue ao objeto `chain_with_memory` (`RunnableWithMessageHistory`).
3.  **BUSCA DO HISTÓRICO:**
    - O `RunnableWithMessageHistory` pega o `session_id` e chama a função `get_session_history`.

    > **É DAQUI QUE O "HISTÓRICO" É PEGO.** Vamos detalhar a função chamada:

    
    **Componente Detalhado: `get_session_history(session_id: str)`**

    - **Propósito:** Função "getter" exigida pelo `RunnableWithMessageHistory`. Ela fornece o objeto de histórico de mensagens para uma sessão específica.
    - **Entrada:** `session_id (str)`: O identificador da sessão.
    - **Lógica Principal:**
        1. Chama `get_session_data()` para garantir que a sessão exista no `store`.
        2. Acessa o dicionário da sessão e retorna apenas o valor da chave `"history"`.
    - **Saída:** `ChatMessageHistory`: O objeto que contém a lista de mensagens daquela conversa.
    

4.  **Injeção do Histórico:** O `RunnableWithMessageHistory` pega o histórico retornado e o injeta no "pacote de dados", criando um dicionário como `{"question": "...", "chat_history": [...]}`.

---
## Passo 4: A Linha de Montagem da IA (Execução da `main_chain`)
---
1.  **Ação do Código:** O "pacote completo" (pergunta + histórico) é finalmente passado para a `main_chain`.
2.  **Ordem dos Acontecimentos Interna:**

    **a) Roteador (`router_chain`):** Recebe o pacote, classifica a intenção e adiciona o `topic`.

    
    **Componente Detalhado: `router_chain`**

    - **Propósito:** Classificar a intenção do usuário para decidir se a pergunta requer uma consulta ao banco de dados ou se é uma conversa casual.
    - **Fluxo Detalhado:**
        1. Recebe a pergunta do usuário e o histórico da conversa.
        2. Monta o `ROUTER_PROMPT` com essas informações.
        3. Envia o prompt para um LLM.
        4. O `StrOutputParser` garante que a saída seja uma string de texto limpa.
    - **Exemplo de Entrada:**
      ```json
      {
          "question": "e qual o total de mercadorias dele?",
          "chat_history": ["Human: Qual o cliente com mais operações? AI: O cliente é 'Porto'."]
      }
      ```
    - **Exemplo de Saída:**
      ```
      "consulta_ao_banco_de_dados"
      ```
    

    **b) Desvio (`branch`):** Lê o `topic` e direciona o pacote para a `sql_chain`.

    
    **Componente Detalhado: `branch` (`RunnableBranch`)**

    - **Propósito:** Funcionar como um `if/elif/else` dentro da sua cadeia. Ele examina o `topic` e decide qual sub-cadeia (`sql_chain` ou `simple_chat_chain`) deve ser executada.
    - **Como Funciona:**
        1. Recebe o dicionário de dados que já contém a chave `topic`.
        2. Testa a primeira condição: se `"consulta_ao_banco_de_dados"` está no `topic`. Se sim, invoca a `sql_chain`.
        3. Se não, testa a segunda condição: se `"saudacao_ou_conversa_simples"` está no `topic`. Se sim, invoca a `simple_chat_chain`.
        4. Se nenhuma for atendida, invoca a `fallback_chain`.
    

    **c) Rephraser (`rephrasing_chain`):** Recebe o pacote, lê a pergunta e o histórico, e gera a `standalone_question`.

    
    **Componente Detalhado: `rephrasing_chain`**

    - **Propósito:** Atuar como o "Especialista em Contexto". Transforma uma pergunta ambígua em uma pergunta completa e autônoma.
    - **Fluxo Detalhado:**
        1. Recebe a pergunta do usuário e o histórico da conversa.
        2. Usa o `REPHRASER_PROMPT` (`FewShotPromptTemplate`) para instruir o LLM.
        3. O LLM analisa o histórico e a nova pergunta para resolver o contexto.
        4. O `StrOutputParser` extrai a pergunta reescrita como uma string.
    - **Exemplo de Entrada:**
      ```json
      {
          "question": "e qual o total de mercadorias dele?",
          "chat_history": ["Human: Qual o cliente com mais operações? AI: O cliente é 'Porto'."]
      }
      ```
    - **Exemplo de Saída:**
      ```
      "Qual o valor total de mercadorias do cliente 'Porto'?"
      ```
    

    **d) Geração SQL (`sql_generation_chain`):** Recebe a `standalone_question` e gera a `generated_sql`.

    
    **Componente Detalhado: `sql_generation_chain`**

    - **Propósito:** Atuar como o "Engenheiro SQL". Traduz uma pergunta clara em uma query SQL válida.
    - **Fluxo Detalhado:**
        1. Recebe a pergunta já reescrita (autônoma).
        2. Adiciona o schema do banco de dados ao contexto.
        3. Monta o `SQL_PROMPT` com a pergunta e o schema.
        4. Envia para um LLM para gerar o código SQL.
        5. O `StrOutputParser` extrai a query SQL como uma string.
    - **Exemplo de Entrada:**
      ```json
      {
          "question": "Qual o valor total de mercadorias do cliente 'Porto'?"
      }
      ```
    - **Exemplo de Saída:**
      ```sql
      "SELECT SUM(o.valor_mercadoria) FROM operacoes_logisticas o JOIN clientes c ON o.cliente_id = c.id WHERE c.nome_razao_social = 'Porto'"
      ```
    

    **e) Execução SQL (`execute_sql_query`):** Executa a `generated_sql` e obtém o `query_result`.

    
    **Componente Detalhado: `execute_sql_query(query: str)`**

    - **Propósito:** Executar de forma segura uma query SQL no banco de dados, atuando como uma camada de proteção.
    - **Entrada:** `query (str)`: A query SQL gerada pelo LLM.
    - **Lógica Principal:**
        - **Segurança:** Adiciona `LIMIT 100` a queries `SELECT` para prevenir busca de dados em massa.
        - **Execução:** Usa `db_instance.run(query)`.
        - **Tratamento de Vazio:** Se o resultado for `[]`, retorna `"RESULTADO_VAZIO: ..."`.
        - **Tratamento de Erro:** Se a query falhar, retorna `"ERRO_DB: ..."`.
    - **Saída:** `str`: O resultado do banco ou uma mensagem de estado.
    

    **f) Resposta Final (`final_response_chain`):** Recebe o `query_result` e a `standalone_question` e gera o `final_response_json`.

    
    **Componente Detalhado: `final_response_chain`**

    - **Propósito:** Atuar como o "Analista de Dados". Converte o resultado bruto do banco em uma resposta JSON amigável.
    - **Fluxo Detalhado:**
        1. Prepara as chaves `result`, `question` e `format_instructions`.
        2. Monta o `FINAL_ANSWER_PROMPT`.
        3. Envia para um LLM que decide entre texto ou gráfico e gera uma string JSON.
        4. O `JsonOutputParser` valida e converte a string em um dicionário Python.
    - **Exemplo de Entrada:**
      ```json
      {
          "question": "Qual o valor total de mercadorias do cliente 'Porto'?",
          "query_result": "[{'sum': 108396678.02}]"
      }
      ```
    - **Exemplo de Saída:**
      ```json
      {
          "type": "text",
          "content": "O valor total de mercadorias para o cliente 'Porto' é de R$ 108.396.678,02."
      }
      ```
    

    **g) Formatação:** Funções auxiliares combinam e formatam a saída final.

---
## Passo 5: O Retorno e a Persistência
---
1.  **Ação do Código:** A `main_chain` termina e retorna seu dicionário de saída.
2.  **Lógica Principal:** A execução volta para o `chain_with_memory`.
3.  **Salvar Memória:** O `chain_with_memory` pega a pergunta original e a `history_message` e as salva de volta no `store` usando o `session_id`.
4.  **Retorno para a API:** O dicionário de saída é retornado para a função `chat_endpoint`.

---
## Passo 6: A Resposta Final (Backend para Frontend)
---
1.  **Origem:** A execução volta para `api.py`.
2.  **Ação do Código:** A função `chat_endpoint` recebe o resultado, adiciona `response_time` e `session_id` e retorna o JSON final.

    > **É AQUI QUE A SAÍDA FINAL É DEFINIDA.** Vamos detalhar os formatos possíveis:

    
    **Componente Detalhado: Exemplos de Saída do Endpoint `/chat`**

    **1. Resposta de Texto Simples:**
    ```json
    {
        "type": "text",
        "content": "A operação com o código de rastreio 'VV820450103ER' está com o status 'EM_TRANSITO'.",
        "generated_sql": "SELECT status FROM operacoes_logisticas WHERE codigo_rastreio = 'VV820450103ER'",
        "response_time": "3.14",
        "session_id": "f9087639-1f3a-48fd-9eb7-53318fc04643"
    }
    ```

    **2. Resposta com Gráfico:**
    ```json
    {
        "type": "chart",
        "chart_type": "bar",
        "title": "Valor Total de Frete por Estado de Destino",
        "data": [{"uf_destino": "SP", "valor_total_frete": 106087014.78}],
        "x_axis": "uf_destino",
        "y_axis": ["valor_total_frete"],
        "y_axis_label": "Valor Total Frete (R$)",
        "generated_sql": "SELECT uf_destino, SUM(valor_frete)...",
        "response_time": "4.51",
        "session_id": "f9087639-1f3a-48fd-9eb7-53318fc04643"
    }
    ```
    

---
## Passo 7: Exibição na Tela (Frontend)
---
1.  **Origem:** `frontend/src/pages/Chat.js`.
2.  **Ação do Código:** A chamada `axios` recebe a resposta. A função `handleSubmit` atualiza o estado `messages` com a resposta do bot, fazendo com que o novo `ChatMessage` seja renderizado na tela para o usuário ver.