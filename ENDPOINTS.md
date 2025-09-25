# Endpoints 

- [Endpoints](#endpoints)
- [`backend/app/api/dashboard.py`](#backendappapidashboardpy)
  - [ENDPOINT GET - `/kpis`](#endpoint-get---kpis)
  - [ENDPOINT GET - `/operacoes_por_status`](#endpoint-get---operacoes_por_status)
  - [ENDPOINT GET - `/valor_frete_por_uf`](#endpoint-get---valor_frete_por_uf)
  - [ENDPOINT GET - `/operacoes_por_dia`](#endpoint-get---operacoes_por_dia)
  - [ENDPOINT GET - `/top_clientes_por_valor`](#endpoint-get---top_clientes_por_valor)


# `backend/app/api/dashboard.py`

---

## ENDPOINT GET - `/kpis`

**Retorna os principais KPIs (Key Performance Indicators) do dashboard logístico.**

**Descrição:**  
Este endpoint consulta o banco de dados `operacoes_logisticas` e retorna métricas agregadas de desempenho das operações logísticas. Para otimizar a performance, os resultados são armazenados em cache; se os dados já estiverem em cache, o log indicará `CACHE HIT` e a query não será executada novamente.

**Parâmetros de entrada:**  
- Nenhum parâmetro é necessário.  
- O endpoint depende do cursor do banco de dados (`cur`) injetado via `Depends(get_db_cursor)` no FastAPI.

**Exemplo de Request:**  
```http
GET /kpis
```

**Resposta de Sucesso (HTTP 200):**  
Um JSON com os seguintes campos:

| Campo                     | Tipo     | Descrição                                           |
|----------------------------|---------|---------------------------------------------------|
| `total_operacoes`          | int     | Número total de operações registradas            |
| `operacoes_entregues`      | int     | Número de operações com status `ENTREGUE`        |
| `operacoes_em_transito`    | int     | Número de operações com status `EM_TRANSITO`     |
| `valor_total_mercadorias`  | float   | Soma do valor das mercadorias de todas as operações |

**Exemplo de Response:**  
```json
{
  "total_operacoes": 1200,
  "operacoes_entregues": 900,
  "operacoes_em_transito": 300,
  "valor_total_mercadorias": 157500.75
}
```

**Tratamento de Erros:**  
- Retorna `HTTP 500` com a mensagem `"Erro interno ao processar KPIs."` caso ocorra algum problema ao acessar o banco ou processar os dados.

**Observações:**  
- O valor de `valor_total_mercadorias` é convertido de `Decimal` para `float` para compatibilidade com JSON.  
- Logs indicam quando os dados não estão em cache (`CACHE MISS`) e quando são servidos do cache (`CACHE HIT`).

---

## ENDPOINT GET - `/operacoes_por_status`

**Retorna a contagem de operações logísticas agrupadas por status.** 

**Descrição:**  
Este endpoint consulta o banco de dados `operacoes_logisticas` e retorna a quantidade de operações em cada status (`ENTREGUE`, `EM_TRANSITO`, etc.). As colunas da query já são renomeadas para `name` e `value`, facilitando o uso direto pelo frontend. Para otimizar a performance, os resultados são armazenados em cache; se os dados já estiverem em cache, o log indicará `CACHE HIT` e a query não será executada novamente.

**Parâmetros de entrada:**  
- Nenhum parâmetro é necessário.  
- O endpoint depende do cursor do banco de dados (`cur`) injetado via `Depends(get_db_cursor)` no FastAPI.

**Exemplo de Request:**  
```http
GET /operacoes_por_status
```

**Resposta de Sucesso (HTTP 200):**  
Um JSON com os seguintes campos:

| Campo   | Tipo | Descrição                               |
|---------|------|-----------------------------------------|
| `name`  | str  | Status da operação (`ENTREGUE`, `EM_TRANSITO`, etc.) |
| `value` | int  | Quantidade de operações naquele status  |

**Exemplo de Response:**  
```json
[
  { "name": "ENTREGUE", "value": 900 },
  { "name": "EM_TRANSITO", "value": 300 },
  { "name": "PENDENTE", "value": 50 }
]
```

**Tratamento de Erros:**  
- Retorna `HTTP 500` com a mensagem `"Erro interno ao processar operações por status."` caso ocorra algum problema ao acessar o banco ou processar os dados.

**Observações:**  
- A query já retorna os resultados ordenados pela quantidade (`value`) em ordem decrescente.  
- Logs indicam quando os dados não estão em cache (`CACHE MISS`) e quando são servidos do cache (`CACHE HIT`).

---

## ENDPOINT GET - `/valor_frete_por_uf`

**Retorna os valores totais de frete agrupados por UF de destino**.

**Descrição:**  
Este endpoint consulta o banco de dados `operacoes_logisticas` e retorna a soma do valor do frete por UF de destino. Apenas as UFs com valor de frete não nulo são consideradas. Para otimizar a performance, os resultados são armazenados em cache; se os dados já estiverem em cache, o log indicará `CACHE HIT` e a query não será executada novamente.

**Parâmetros de entrada:**  
- Nenhum parâmetro é necessário.  
- O endpoint depende do cursor do banco de dados (`cur`) injetado via `Depends(get_db_cursor)` no FastAPI.

**Exemplo de Request:**  
```http
GET /valor_frete_por_uf
```

**Resposta de Sucesso (HTTP 200):**  
Um JSON com os seguintes campos:

| Campo   | Tipo  | Descrição                                   |
|---------|-------|---------------------------------------------|
| `name`  | str   | UF de destino da operação                    |
| `value` | float | Soma do valor do frete naquela UF           |

**Exemplo de Response:**  
```json
[
  { "name": "SP", "value": 25000.50 },
  { "name": "RJ", "value": 18000.75 },
  { "name": "MG", "value": 12000.00 }
]
```

**Tratamento de Erros:**  
- Retorna `HTTP 500` com a mensagem `"Erro interno ao processar valor de frete por UF."` caso ocorra algum problema ao acessar o banco ou processar os dados.

**Observações:**  
- O valor de `value` é convertido de `Decimal` para `float` para compatibilidade com JSON.  
- Os resultados são limitados às 10 UFs com maior valor total de frete.  
- Logs indicam quando os dados não estão em cache (`CACHE MISS`) e quando são servidos do cache (`CACHE HIT`).

---

## ENDPOINT GET - `/operacoes_por_dia`

**Retorna a quantidade de operações logísticas agrupadas por dia nos últimos 30 dias.**

**Descrição:**  
Este endpoint consulta o banco de dados `operacoes_logisticas` e retorna o total de operações emitidas por dia. As datas são formatadas no padrão `dd/mm` para facilitar a visualização no frontend. Para otimizar a performance, os resultados são armazenados em cache; se os dados já estiverem em cache, o log indicará `CACHE HIT` e a query não será executada novamente.

**Parâmetros de entrada:**  
- Nenhum parâmetro é necessário.  
- O endpoint depende do cursor do banco de dados (`cur`) injetado via `Depends(get_db_cursor)` no FastAPI.

**Exemplo de Request:**  
```http
GET /operacoes_por_dia
```

**Resposta de Sucesso (HTTP 200):**  
Um JSON com os seguintes campos:

| Campo   | Tipo | Descrição                             |
|---------|------|---------------------------------------|
| `name`  | str  | Data da operação (formato `dd/mm`)     |
| `value` | int  | Quantidade de operações naquele dia    |

**Exemplo de Response:**  
```json
[
  { "name": "01/09", "value": 40 },
  { "name": "02/09", "value": 35 },
  { "name": "03/09", "value": 50 }
]
```

**Tratamento de Erros:**  
- Retorna `HTTP 500` com a mensagem `"Erro interno ao processar operações por dia."` caso ocorra algum problema ao acessar o banco ou processar os dados.

**Observações:**  
- Apenas os últimos 30 dias são considerados.  
- A data é formatada para `dd/mm` a partir do tipo `datetime.date` do PostgreSQL.  
- Logs indicam quando os dados não estão em cache (`CACHE MISS`) e quando são servidos do cache (`CACHE HIT`).

---

## ENDPOINT GET - `/top_clientes_por_valor`

**Retorna os principais clientes por valor total de mercadorias.**

**Descrição:**  
Este endpoint consulta o banco de dados `operacoes_logisticas` e retorna a soma do valor das mercadorias agrupadas por cliente, mostrando os 5 clientes com maior valor. Para otimizar a performance, os resultados são armazenados em cache; se os dados já estiverem em cache, o log indicará `CACHE HIT` e a query não será executada novamente.

**Parâmetros de entrada:**  
- Nenhum parâmetro é necessário.  
- O endpoint depende do cursor do banco de dados (`cur`) injetado via `Depends(get_db_cursor)` no FastAPI.

**Exemplo de Request:**  
```http
GET /top_clientes_por_valor
```

**Resposta de Sucesso (HTTP 200):**  
Um JSON com os seguintes campos:

| Campo   | Tipo  | Descrição                                  |
|---------|-------|--------------------------------------------|
| `name`  | str   | Nome ou razão social do cliente            |
| `value` | float | Soma do valor das mercadorias do cliente   |

**Exemplo de Response:**  
```json
[
  { "name": "Cliente A", "value": 50000.75 },
  { "name": "Cliente B", "value": 42000.00 },
  { "name": "Cliente C", "value": 38000.50 }
]
```

**Tratamento de Erros:**  
- Retorna `HTTP 500` com a mensagem `"Erro interno ao processar top clientes."` caso ocorra algum problema ao acessar o banco ou processar os dados.

**Observações:**  
- O valor de `value` é convertido de `Decimal` para `float` para compatibilidade com JSON.  
- Apenas os 5 clientes com maior valor total de mercadorias são retornados.  
- Logs indicam quando os dados não estão em cache (`CACHE MISS`) e quando são servidos do cache (`CACHE HIT`).