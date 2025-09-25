# SuppBot - BI

> SUPPBOT BI é uma solução de Business Intelligence conversacional para logística, baseada em IA generativa e RAG (Retrieval-Augmented Generation). O sistema utiliza LLMs para interpretar perguntas em linguagem natural, gerar consultas SQL dinâmicas e entregar respostas precisas e contextualizadas, incluindo gráficos e KPIs. Com arquitetura modular de prompts e memória de conversa, SUPPBOT BI oferece uma interface inteligente para análise avançada de dados logísticos via dashboard e principalmente chatbot.

## Índice
- [SuppBot - BI](#suppbot---bi)
  - [Índice](#índice)
  - [🛠️ Tecnologias Usadas](#️-tecnologias-usadas)
    - [**Geral**](#geral)
    - [**Frontend**](#frontend)
    - [**Backend**](#backend)
    - [Modelos LLM:](#modelos-llm)
  - [Estrutura do Projeto](#estrutura-do-projeto)
  - [Updates](#updates)
  - [Funcionamento](#funcionamento)
    - [`backend/app/api/dashboard.py`](#backendappapidashboardpy)

---

## 🛠️ Tecnologias Usadas

### **Geral**
- [Node.js](https://nodejs.org/) (**18.3.1**)
- [npm](https://www.npmjs.com/) 
- [Python](https://www.python.org/) (**3.12**)
- [PostgreSQL](https://www.postgresql.org/) 
- [Git](https://git-scm.com/)

---

### **Frontend**
O frontend foi criado com **React** e utiliza:  
- `react-router-dom` (navegação entre páginas)  
- `axios` (requisições HTTP)  
- `recharts` (gráficos e visualizações)  
- `react-icons` (ícones)  
- `uuid` (geração de IDs)  
- `react-scripts` (scripts de build e desenvolvimento)  

---

### **Backend**
O backend foi construído com **FastAPI** + **LangChain**, incluindo:  
- `fastapi` (API backend)  
- `uvicorn` (servidor ASGI)  
- `sqlalchemy` + `psycopg2-binary` (integração com PostgreSQL)  
- `langchain`, `langchain-core`, `langchain-community`, `langchain-groq` (IA e LLMs)  
- `requests` / `httpx` (requisições HTTP)  
- `pydantic` (validação de dados)  
- `faker` (dados de teste)  

### Modelos LLM:
-  `llama-3.3-70b-versatile` - Para geração das queries
-  `llama-3.1-8b-instant` - Para as respostas amigáveis

---

## Estrutura do Projeto

```
├── 📁 backend/
│   ├── 📁 app/
│   │   ├── 📁 api/
│   │   │   └── 🐍 dashboard.py
│   │   ├── 📁 chains/
│   │   │   └── 🐍 sql_rag_chain.py
│   │   ├── 📁 core/
│   │   │   ├── 🐍 config.py
│   │   │   ├── 🐍 database.py
│   │   │   └── 🐍 llm.py
│   │   └── 📁 prompts/
│   │       └── 🐍 sql_prompts.py
│   ├── 📁 venv
│   ├── 🔒 .env
│   ├── 🐍 api.py
│   ├── 📄 requirements.txt
│   └── 📄 testes.txt
├── 📁 db_scripts/
│   ├── 🐍 criar_tabelas.py
│   └── 🐍 popular_tabelas.py
├── 📁 frontend/
│   ├── 📁 public/
│   │   ├── 🖼️ favicon.ico
│   │   ├── 🌐 index.html
│   │   ├── 🖼️ logo192.png
│   │   ├── 🖼️ logo512.png
│   │   ├── 📄 manifest.json
│   │   └── 📄 robots.txt
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   │   ├── 📄 ChartComponent.js
│   │   │   ├── 🎨 ChatMessage.css
│   │   │   ├── 📄 ChatMessage.js
│   │   │   ├── 🎨 Navbar.css
│   │   │   └── 📄 Navbar.js
│   │   ├── 📁 pages/
│   │   │   ├── 🎨 Chat.css
│   │   │   ├── 📄 Chat.js
│   │   │   ├── 🎨 Dashboard.css
│   │   │   └── 📄 Dashboard.js
│   │   ├── 🎨 App.css
│   │   ├── 📄 App.js
│   │   ├── 🎨 index.css
│   │   ├── 📄 index.js
│   │   └── 📄 reportWebVitals.js
│   ├── 📄 package-lock.json
│   └── 📄 package.json
├── 📄 .gitattributes
├── 🚫 .gitignore
└── 📖 README.md
```

## Updates

> [!NOTE]
> Versão 1

| Versão | Data       | Mudanças principais               |
|--------|------------|-----------------------------------|
| 1.0    | 25/09/2025 | MVP funcional do SUPPBOT BI       |

---

## Funcionamento

Nesta seção, apresentamos uma visão detalhada de como cada parte do SUPPBOT BI opera, do frontend ao backend. Aqui você encontrará uma explicação clara de como os componentes, scripts e módulos interagem entre si, como os dados fluem do usuário até o banco de dados e de volta, e como a inteligência artificial é utilizada para processar perguntas, gerar consultas SQL e exibir respostas e gráficos.  

O objetivo é fornecer ao leitor uma compreensão completa do funcionamento interno do sistema, permitindo não apenas usar o SUPPBOT BI, mas também entender, manter e expandir seu código com facilidade.

### `backend/app/api/dashboard.py`

> API ROUTER PARA O DASHBOARD Padrões de arquitetura aplicados:
> 1. Connection Pooling: Para reutilizar conexões com o banco de dados e melhorar a performance.
> 2. Cache: Para armazenar em memória os resultados de queries lentas, tornando recargas rápidas.
> 3. Dependency Injection: Padrão do FastAPI para gerenciar recursos (como conexões) de forma segura.

<h4 style="font-size:24px;">Endpoints</h4>

<h5 style="font-size:20px;">/kpis</h5>

Retorna os principais **KPIs (Key Performance Indicators)** do dashboard logístico.

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


<h5 style="font-size:20px;">/operacoes_por_status</h5>

Retorna a contagem de **operações logísticas agrupadas por status**.

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

