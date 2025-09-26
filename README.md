# SuppBot - BI

> SUPPBOT BI é uma solução de Business Intelligence conversacional para logística, baseada em IA generativa e RAG (Retrieval-Augmented Generation). O sistema utiliza LLMs para interpretar perguntas em linguagem natural, gerar consultas SQL dinâmicas e entregar respostas precisas e contextualizadas, incluindo gráficos e KPIs. Com arquitetura modular de prompts e memória de conversa, SUPPBOT BI oferece uma interface inteligente para análise avançada de dados logísticos via dashboard e principalmente chatbot.

# Índice
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
  - [`backend/app/chains/sql_rag_chain.py`](#backendappchainssql_rag_chainpy)

---

# 🛠️ Tecnologias Usadas

## **Geral**
- [Node.js](https://nodejs.org/) (**18.3.1**)
- [npm](https://www.npmjs.com/) 
- [Python](https://www.python.org/) (**3.12**)
- [PostgreSQL](https://www.postgresql.org/) 
- [Git](https://git-scm.com/)

---

## **Frontend**
O frontend foi criado com **React** e utiliza:  
- `react-router-dom` (navegação entre páginas)  
- `axios` (requisições HTTP)  
- `recharts` (gráficos e visualizações)  
- `react-icons` (ícones)  
- `uuid` (geração de IDs)  
- `react-scripts` (scripts de build e desenvolvimento)  

---

## **Backend**
O backend foi construído com **FastAPI** + **LangChain**, incluindo:  
- `fastapi` (API backend)  
- `uvicorn` (servidor ASGI)  
- `sqlalchemy` + `psycopg2-binary` (integração com PostgreSQL)  
- `langchain`, `langchain-core`, `langchain-community`, `langchain-groq` (IA e LLMs)  
- `requests` / `httpx` (requisições HTTP)  
- `pydantic` (validação de dados)  
- `faker` (dados de teste)  

## Modelos LLM:
-  `llama-3.3-70b-versatile` - Para geração das queries
-  `llama-3.1-8b-instant` - Para as respostas amigáveis

---

# Estrutura do Projeto

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

# Updates

> [!NOTE]
> Versão 1

| Versão | Data       | Mudanças principais               |
|--------|------------|-----------------------------------|
| 1.0    | 25/09/2025 | MVP funcional do SUPPBOT BI       |

---

# Funcionamento

Nesta seção, apresentamos uma visão detalhada de como cada parte do SUPPBOT BI opera, do frontend ao backend. Aqui você encontrará uma explicação clara de como os componentes, scripts e módulos interagem entre si, como os dados fluem do usuário até o banco de dados e de volta, e como a inteligência artificial é utilizada para processar perguntas, gerar consultas SQL e exibir respostas e gráficos.  

O objetivo é fornecer ao leitor uma compreensão completa do funcionamento interno do sistema, permitindo não apenas usar o SUPPBOT BI, mas também entender, manter e expandir seu código com facilidade.

---

## `backend/app/api/dashboard.py`

> API ROUTER PARA O DASHBOARD Padrões de arquitetura aplicados:
> 1. Connection Pooling: Para reutilizar conexões com o banco de dados e melhorar a performance.
> 2. Cache: Para armazenar em memória os resultados de queries lentas, tornando recargas rápidas.
> 3. Dependency Injection: Padrão do FastAPI para gerenciar recursos (como conexões) de forma segura.

> [!NOTE]
> Para acessar a documentação dos endpoints acesse:
> [ENDPOINTS](ENDPOINTS.md)

---

## `backend/app/chains/sql_rag_chain.py`

> PROMPT ENGINEERING HUB - O CÉREBRO DA APLICAÇÃO
> 
> ---
> Propósito do Arquivo:
> 
> Este arquivo é o centro de controle da inteligência artificial do sistema. Ele centraliza
> todas as instruções (prompts) que definem as "personalidades" e "habilidades" de cada
> componente de IA, garantindo que a lógica conversacional seja clara, manutenível e
> fácil de aprimorar.
> 
> ---
> Arquitetura e Princípio de Design:
>
> A arquitetura segue o princípio de "Separação de Responsabilidades", onde cada tarefa
> complexa é dividida entre múltiplos "especialistas" de IA que operam em sequência,
> como uma linha de montagem:
> 
> 1. O Porteiro (ROUTER_PROMPT):
> - Responsabilidade: Classificar a intenção do usuário.
> - Ação: Decide se a pergunta é uma conversa casual ou uma consulta ao banco, direcionando-a para o caminho correto.
> 
> 2. O Especialista em Contexto (REPHRASER_PROMPT):
> - Responsabilidade: Resolver ambiguidades e contexto.
> - Ação: Pega perguntas de acompanhamento (ex: "e para ele?") e as reescreve
> como perguntas completas e autônomas, usando o histórico do chat.
> 
> 3. O Engenheiro SQL (SQL_PROMPT):
> - Responsabilidade: Traduzir linguagem natural para SQL.
> - Ação: Recebe a pergunta já clara do Especialista em Contexto e a converte emuma query PostgreSQL precisa, aprendendo com os exemplos fornecidos.
> 
> 4. O Analista de Dados (FINAL_ANSWER_PROMPT):
> - Responsabilidade: Formatar a resposta final para o usuário.
> - Ação: Transforma o resultado bruto do banco de dados em uma resposta amigável,seja em texto ou em um JSON estruturado para gráficos.
> 
> Este design modular torna o sistema mais robusto, previsível e fácil de depurar.