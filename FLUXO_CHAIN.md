# Fluxo de Execução — Cenários de Conversa

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