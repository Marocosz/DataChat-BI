# Fluxo de Execução — Cenários de Conversa

- [Fluxo de Execução — Cenários de Conversa](#fluxo-de-execução--cenários-de-conversa)
  - [Cenário 1: Conversa Simples (Sem Query, Sem Contexto Relevante)](#cenário-1-conversa-simples-sem-query-sem-contexto-relevante)
    - [Fluxo Detalhado:](#fluxo-detalhado)
      - [Entrada e Memória:](#entrada-e-memória)
      - [Estação 1: O Porteiro (router\_chain)](#estação-1-o-porteiro-router_chain)
      - [Estação 2: O Desvio (RunnableBranch)](#estação-2-o-desvio-runnablebranch)
      - [Estação 3: O Assistente Amigável (simple\_chat\_chain)](#estação-3-o-assistente-amigável-simple_chat_chain)
      - [Formatação e Saída:](#formatação-e-saída)
  - [Cenário 2: Consulta Direta ao Banco (Com Query, Sem Contexto de Histórico)](#cenário-2-consulta-direta-ao-banco-com-query-sem-contexto-de-histórico)
    - [Fluxo Detalhado:](#fluxo-detalhado-1)
      - [Entrada e Memória:](#entrada-e-memória-1)
      - [Estação 1: O Porteiro (router\_chain)](#estação-1-o-porteiro-router_chain-1)
      - [Estação 2: O Desvio (RunnableBranch)](#estação-2-o-desvio-runnablebranch-1)
      - [Estação 3: A Linha de Montagem (sql\_chain)](#estação-3-a-linha-de-montagem-sql_chain)
      - [Formatação e Saída:](#formatação-e-saída-1)
  - [Cenário 3: Consulta de Acompanhamento (Com Query e Com Histórico)](#cenário-3-consulta-de-acompanhamento-com-query-e-com-histórico)
    - [Fluxo Detalhado:](#fluxo-detalhado-2)
      - [Entrada e Memória:](#entrada-e-memória-2)
      - [Estação 1: O Porteiro (router\_chain)](#estação-1-o-porteiro-router_chain-2)
      - [Estação 2: O Desvio (RunnableBranch)](#estação-2-o-desvio-runnablebranch-2)
      - [Estação 3: A Linha de Montagem (sql\_chain)](#estação-3-a-linha-de-montagem-sql_chain-1)
      - [Formatação e Saída:](#formatação-e-saída-2)
- [Análise Detalhada das Funções](#análise-detalhada-das-funções)
  - [Funções de Gerenciamento de Sessão](#funções-de-gerenciamento-de-sessão)
    - [1. `get_session_data(session_id: str) -> dict`](#1-get_session_datasession_id-str---dict)
    - [2. `get_session_history(session_id: str) -> ChatMessageHistory`](#2-get_session_historysession_id-str---chatmessagehistory)
    - [3. `update_last_sql(session_id: str, sql: str)`](#3-update_last_sqlsession_id-str-sql-str)
  - [Função Principal de Construção: `create_master_chain()`](#função-principal-de-construção-create_master_chain)
  - [Funções Auxiliares (Definidas Dentro de `create_master_chain`)](#funções-auxiliares-definidas-dentro-de-create_master_chain)
    - [4. `trim_history(data)`](#4-trim_historydata)
    - [5. `execute_sql_query(query: str) -> str`](#5-execute_sql_queryquery-str---str)
    - [6. `format_simple_chat_output(text_content: str) -> dict`](#6-format_simple_chat_outputtext_content-str---dict)
    - [7. `execute_and_log_query(data: dict) -> str`](#7-execute_and_log_querydata-dict---str)
    - [8. `combine_sql_with_response(data: dict) -> dict`](#8-combine_sql_with_responsedata-dict---dict)
    - [9. `format_final_output(chain_output: dict) -> dict`](#9-format_final_outputchain_output-dict---dict)

---

## Cenário 1: Conversa Simples (Sem Query, Sem Contexto Relevante)

Neste cenário, o usuário apenas cumprimenta o bot ou faz uma pergunta casual.

**Exemplo:**

> Usuário diz: "Olá, tudo bem?"

**ID da Sessão:** `sessao-123`

### Fluxo Detalhado:

#### Entrada e Memória:

- A API recebe a pergunta e o `session_id="sessao-123"`.
- O `RunnableWithMessageHistory` é ativado. Ele chama sua função `get_session_history("sessao-123")`, que vai até o store e pega o histórico de mensagens (neste caso, está vazio ou contém conversas anteriores).

#### Estação 1: O Porteiro (router_chain)

- **O que ele recebe:** A pergunta "Olá, tudo bem?" e o histórico da conversa.
- **O que ele faz:** Ele usa o `ROUTER_PROMPT` para perguntar a um LLM:  
  `"Com base neste histórico e na pergunta 'Olá, tudo bem?', qual é a intenção do usuário?"`.
- **Resultado:** O LLM responde com a string `saudacao_ou_conversa_simples`. A cadeia armazena esse resultado na chave `topic`.

#### Estação 2: O Desvio (RunnableBranch)

- **O que ele faz:** Ele olha o valor da chave `topic`.
- A primeira condição (`lambda x: "consulta_ao_banco_de_dados" in x["topic"]`) é falsa.
- A segunda condição (`lambda x: "saudacao_ou_conversa_simples" in x["topic"]`) é verdadeira.
- **Ação:** O `RunnableBranch` desvia a "matéria-prima" (os dados da requisição) para a `simple_chat_chain`.

#### Estação 3: O Assistente Amigável (simple_chat_chain)

- **O que ele faz:** Ele usa o `simple_chat_prompt_with_history`, que instrui o LLM a agir como um assistente amigável.
- **Resultado:** O LLM gera uma resposta textual, como:  
  `"Olá! Tudo bem por aqui. Como posso te ajudar com os dados de logística hoje?"`.

#### Formatação e Saída:

- A função `format_simple_chat_output` pega o texto e o envolve em um JSON, adicionando a chave `"generated_sql": "Nenhuma query foi necessária..."`.
- O `format_final_output` prepara o pacote final para a API.
- O `RunnableWithMessageHistory` salva a pergunta do usuário e a resposta do bot no histórico da `sessao-123`.
- O frontend recebe a resposta JSON.

---

## Cenário 2: Consulta Direta ao Banco (Com Query, Sem Contexto de Histórico)

Aqui, o usuário faz uma pergunta completa que não depende de nada que foi dito antes.

**Exemplo:**

> Usuário diz: "Qual o cliente com o maior número de operações canceladas?"

**ID da Sessão:** `sessao-456`

### Fluxo Detalhado:

#### Entrada e Memória:
- O histórico para `sessao-456` é carregado.

#### Estação 1: O Porteiro (router_chain)
- **O que ele recebe:** A pergunta e o histórico.
- **O que ele faz:** Usa o `ROUTER_PROMPT`. O LLM vê palavras como "cliente", "operações", "maior número" e classifica a intenção.
- **Resultado:** O `topic` é definido como `consulta_ao_banco_de_dados`.

#### Estação 2: O Desvio (RunnableBranch)
- A primeira condição (`lambda x: "consulta_ao_banco_de_dados" in x["topic"]`) é verdadeira.
- **Ação:** A requisição é enviada para a `sql_chain`, a nossa linha de montagem principal.

#### Estação 3: A Linha de Montagem (sql_chain)

**Passo 3a: O Especialista em Contexto (rephrasing_chain)**

- **O que ele recebe:** A pergunta `"Qual o cliente com o maior número de operações canceladas?"` e o histórico.
- **O que ele faz:** Usa o `REPHRASER_PROMPT`. O LLM percebe que a pergunta já está completa e não precisa de contexto.
- **Resultado:** Ele retorna a própria pergunta, sem alterações. O log no seu terminal mostra: `Pergunta Reescrita pelo Rephraser: 'Qual o cliente com...'`. O resultado é salvo na chave `standalone_question`.

**Passo 3b: O Engenheiro SQL (sql_generation_chain)**

- **O que ele recebe:** A `standalone_question` e o esquema do banco de dados. Note que ele não recebe mais o histórico!
- **O que ele faz:** Usa o `SQL_PROMPT` e os `FEW_SHOT_EXAMPLES` para traduzir a pergunta clara em SQL.
- **Resultado:** Ele gera a query SQL:  
  `SELECT c.nome_razao_social... WHERE o.status = 'CANCELADO' GROUP BY ... ORDER BY ... LIMIT 1;`. O resultado é salvo na chave `generated_sql`.

**Passo 3c: O Executor (execute_sql_query)**

- **O que ele faz:** Pega a `generated_sql` e a executa no banco de dados de forma segura.
- **Resultado:** Retorna os dados brutos, por exemplo:  
  `[{ 'nome_razao_social': 'Pimenta', 'total_operacoes': 218 }]`. O resultado é salvo na chave `query_result`.

**Passo 3d: O Analista de Dados (final_response_chain)**

- **O que ele recebe:** A `standalone_question` e o `query_result`.
- **O que ele faz:** Usa o `FINAL_ANSWER_PROMPT` para transformar os dados brutos em uma resposta amigável formatada em JSON.
- **Resultado:**  
```json
{"type": "text", "content": "O cliente com o maior número de operações canceladas é 'Pimenta', com 218 operações."}
```
O resultado é salvo na chave `final_response_json`.

#### Formatação e Saída:

- A função `combine_sql_with_response` adiciona a `generated_sql` ao JSON final.
- O `RunnableWithMessageHistory` salva a pergunta do usuário e a resposta do bot. Além disso, a função `update_last_sql` salva a query SQL gerada na memória da sessão.
- O frontend recebe a resposta JSON completa.

---

## Cenário 3: Consulta de Acompanhamento (Com Query e Com Histórico)

Este é o cenário mais complexo e onde a nova arquitetura realmente brilha.

**Exemplo:**

- Histórico da `sessao-456`: Já contém a pergunta e resposta do Cenário 2.
- Usuário diz: `"e qual o valor total de mercadorias dele?"`
- **ID da Sessão:** `sessao-456` (o mesmo de antes)

### Fluxo Detalhado:

#### Entrada e Memória:
- O `RunnableWithMessageHistory` carrega o histórico da `sessao-456`, que agora contém a conversa sobre o cliente "Pimenta".

#### Estação 1: O Porteiro (router_chain)
- **O que ele recebe:** A pergunta curta `"e qual o valor total de mercadorias dele?"` e o histórico rico em contexto.
- **O que ele faz:** Usa o `ROUTER_PROMPT`. O LLM vê a pergunta incompleta e o histórico de consulta e entende que é uma continuação.
- **Resultado:** O `topic` é `consulta_ao_banco_de_dados`.

#### Estação 2: O Desvio (RunnableBranch)
- A requisição é enviada para a `sql_chain`.

#### Estação 3: A Linha de Montagem (sql_chain)

**Passo 3a: O Especialista em Contexto (rephrasing_chain)**

- **O que ele recebe:** A pergunta ambígua `"e qual o valor total de mercadorias dele?"` e o histórico contendo `"O cliente com o maior número de operações canceladas é 'Pimenta'"`.
- **O que ele faz:** Usa o `REPHRASER_PROMPT`. O LLM agora tem tudo que precisa. Ele entende que "dele" se refere a "Pimenta".
- **Resultado:** Ele gera uma pergunta nova, clara e completa:  
  `"Qual o valor total de mercadorias do cliente 'Pimenta'?"`. Esta é a etapa que falhava antes e agora funciona.

**Passo 3b: O Engenheiro SQL (sql_generation_chain)**

- **O que ele recebe:** A pergunta perfeita: `"Qual o valor total de mercadorias do cliente 'Pimenta'?"`.
- **O que ele faz:** Como a pergunta é clara, a tradução para SQL é direta e livre de erros.
- **Resultado:** Ele gera a query: 
  
```sql
SELECT SUM(o.valor_mercadoria)
FROM operacoes_logisticas o
JOIN clientes c ON o.cliente_id = c.id
WHERE c.nome_razao_social = 'Pimenta';
```

- *(Passos 3c e 3d continuam como no Cenário 2, mas com a nova query e resultado).*

#### Formatação e Saída:
- O ciclo se completa como antes, e o frontend recebe a resposta correta para a pergunta de acompanhamento.

---
---

# Análise Detalhada das Funções

O arquivo é dividido em duas partes: as funções de alto nível que gerenciam o estado da sessão e a grande função `create_master_chain()` que constrói toda a lógica e contém suas próprias funções auxiliares.

---

## Funções de Gerenciamento de Sessão

Estas são as funções que interagem com o dicionário **store** para dar memória à aplicação.

### 1. `get_session_data(session_id: str) -> dict`
**Propósito:** É a porta de entrada para o store. Garante que sempre haja um registro para uma sessão, criando um novo se for a primeira vez que o ID aparece.

**Entrada:**
- `session_id (str)`: O identificador único da sessão, vindo do frontend.

**Lógica Principal:**
- Verifica se a `session_id` já existe como uma chave no dicionário **store**.
- Se não existir, cria uma nova entrada no store para esse ID.  
  A nova entrada é um dicionário contendo um `ChatMessageHistory()` vazio e um valor padrão para `last_sql`.
- Se já existir, não faz nada.

**Saída:**
- `dict`: Retorna o dicionário completo da sessão (`{"history": ..., "last_sql": ...}`).

---

### 2. `get_session_history(session_id: str) -> ChatMessageHistory`
**Propósito:** Função específica para o LangChain. O `RunnableWithMessageHistory` a utiliza para carregar o histórico de mensagens de uma sessão no início de cada turno.

**Entrada:**
- `session_id (str)`: O identificador da sessão.

**Lógica Principal:**
- Chama `get_session_data()` para garantir que a sessão exista.
- Acessa o dicionário da sessão e retorna apenas o valor da chave `"history"`.

**Saída:**
- `ChatMessageHistory`: O objeto que contém a lista de mensagens daquela conversa.

---

### 3. `update_last_sql(session_id: str, sql: str)`
**Propósito:** Salvar a última query SQL bem-sucedida na memória de "trabalho" de uma sessão.

**Entrada:**
- `session_id (str)`: O identificador da sessão.
- `sql (str)`: A string da query SQL que foi gerada e executada.

**Lógica Principal:**
- Verifica se a sessão existe no **store**.
- Verifica se a string `sql` não é vazia e não contém uma mensagem de erro.
- Se as condições forem atendidas, atualiza o valor da chave `"last_sql"` no dicionário da sessão.

**Saída:**
- Nenhuma (a função modifica o **store** diretamente, um efeito colateral).

---

## Função Principal de Construção: `create_master_chain()`

Esta função gigante é uma "fábrica" que constrói e conecta todos os componentes da linha de montagem.

**Propósito:** Orquestrar a criação de todas as sub-cadeias (router, rephraser, sql, etc.) e conectá-las em uma `Runnable` principal e com memória.

**Entrada:** Nenhuma.

**Saída:**
- `Runnable`: A cadeia completa e pronta para uso (`chain_with_memory`), que a API irá invocar.

---

## Funções Auxiliares (Definidas Dentro de `create_master_chain`)

Estas funções são definidas localmente dentro de `create_master_chain` e usadas como "ferramentas" na construção da linha de montagem.

### 4. `trim_history(data)`
**Propósito:** Manter o histórico da conversa com um tamanho fixo para evitar exceder o limite de tokens dos LLMs.

**Entrada:**
- `data (dict)`: O dicionário de dados que flui pela cadeia, que contém a chave `"chat_history"`.

**Lógica Principal:**
- Pega a lista de mensagens do `"chat_history"`.
- Se a lista tiver mais de `k (6)` mensagens, ela a "fatia", mantendo apenas as últimas 6.

**Saída:**
- `dict`: O mesmo dicionário `data`, mas com a chave `"chat_history"` potencialmente encurtada.

---

### 5. `execute_sql_query(query: str) -> str`
**Propósito:** Executar de forma segura uma query SQL no banco de dados, atuando como uma camada de proteção.

**Entrada:**
- `query (str)`: A query SQL gerada pelo LLM.

**Lógica Principal:**
- **Segurança:** Adiciona `LIMIT 100` a queries `SELECT` que não sejam de agregação para prevenir a busca de dados em massa.
- **Execução:** Usa `db_instance.run(query)` para executar a query no banco.
- **Tratamento de Vazio:** Se o resultado for vazio (`[]`), retorna a string padronizada `"RESULTADO_VAZIO: ..."`.
- **Tratamento de Erro:** Se a execução da query falhar, o bloco `except` captura o erro e retorna a string `"ERRO_DB: ..."`.

**Saída:**
- `str`: Uma string contendo o resultado do banco, ou uma das mensagens de estado (vazio/erro).

---

### 6. `format_simple_chat_output(text_content: str) -> dict`
**Propósito:** Padronizar a saída da cadeia de conversa simples para que ela tenha a mesma estrutura JSON da cadeia SQL.

**Entrada:**
- `text_content (str)`: O texto puro gerado pelo LLM na conversa simples.

**Saída:**
- `dict`: Um dicionário no formato `{"type": "text", "content": ..., "generated_sql": "..."}`.

---

### 7. `execute_and_log_query(data: dict) -> str`
**Propósito:** Uma pequena função "wrapper" que conecta a `execute_sql_query` à cadeia e adiciona um log extra.

**Entrada:**
- `data (dict)`: O dicionário da cadeia, que deve conter a chave `"generated_sql"`.

**Saída:**
- `str`: O resultado da execução da query (o mesmo que a saída da `execute_sql_query`).

---

### 8. `combine_sql_with_response(data: dict) -> dict`
**Propósito:** Juntar a resposta final (o JSON do `final_response_chain`) com a query SQL gerada, criando o objeto JSON completo que será enviado ao frontend.

**Entrada:**
- `data (dict)`: O dicionário da cadeia, contendo `"final_response_json"` e `"generated_sql"`.

**Saída:**
- `dict`: O mesmo dicionário de `final_response_json`, mas agora com a chave `"generated_sql"` adicionada.

---

### 9. `format_final_output(chain_output: dict) -> dict`
**Propósito:** Preparar o pacote final de saída da cadeia, criando duas versões da resposta.

**Entrada:**
- `chain_output (dict)`: O dicionário final produzido por qualquer um dos ramos (`simple_chat_chain` ou `sql_chain`).

**Lógica Principal:**
- Cria uma versão em texto puro da resposta.  
- Se for um gráfico, cria um texto descritivo (ex: `"Gerei um gráfico para você..."`).

**Saída:**
- `dict`: Um novo dicionário com duas chaves:
  - `"api_response"`: O dicionário JSON completo para o frontend.
  - `"history_message"`: A versão em texto simplificada, que será salva no histórico da conversa.
