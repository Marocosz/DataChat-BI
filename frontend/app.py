# frontend/app.py

import streamlit as st
import requests

# --- Configurações ---
# URL da API do backend
API_URL = "http://localhost:8000/api/v1/chat/query"

# Configuração da página do Streamlit (título, ícone, layout)
st.set_page_config(
    page_title="Assistente de Catálogo de Dados",
    page_icon="🧠",
    layout="wide"  # Layout "wide" é melhor para exibir respostas com mais dados
)

# --- Título e Descrição ---
st.title("🧠 Assistente de Catálogo de Dados")
st.caption("Pergunte-me sobre esquemas, tabelas e colunas do nosso banco de dados!")

# --- Gerenciamento do Estado da Sessão (Session State) ---
# Inicializa o histórico de mensagens se ele ainda não existir.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou seu assistente para explorar nosso catálogo de dados. O que você gostaria de saber?"}
    ]
# Inicializa o ID da sessão se ele ainda não existir.
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# --- Exibição do Histórico de Chat ---
# Percorre a lista de mensagens no estado da sessão e exibe cada uma na tela.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Captura e Processamento do Input do Usuário ---
# Cria a caixa de input de chat fixa na parte inferior da página.
if prompt := st.chat_input("Onde posso encontrar o ID do cliente?"):
    # Adiciona a mensagem do usuário ao histórico e à tela imediatamente.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepara para mostrar a resposta do assistente.
    with st.chat_message("assistant"):
        # Mostra um "spinner" de carregamento enquanto aguarda a resposta da API.
        with st.spinner("Analisando metadados..."):
            try:
                # Prepara o corpo (payload) da requisição com a pergunta e o ID da sessão atual.
                payload = {
                    "query": prompt,
                    "session_id": st.session_state.session_id
                }

                # Envia a requisição POST para a API do backend.
                response = requests.post(API_URL, json=payload)
                response.raise_for_status()  # Gera um erro se a resposta for um código de falha (4xx ou 5xx).

                # Extrai os dados da resposta JSON.
                api_data = response.json()
                api_answer = api_data["answer"]
                
                # ATUALIZA o ID da sessão com o valor retornado pela API.
                # Isso é crucial para manter a continuidade da conversa.
                st.session_state.session_id = api_data["session_id"]
                
                # Exibe a resposta da API diretamente na tela.
                st.markdown(api_answer)

            except requests.exceptions.RequestException as e:
                # Trata erros de conexão com a API ou falhas da API.
                api_answer = f"**Erro de comunicação com a API.** Verifique se o backend está rodando.\n\n*Detalhes: {e}*"
                st.error(api_answer)
            except Exception as e:
                # Trata outros erros inesperados que possam ocorrer.
                api_answer = f"**Ocorreu um erro inesperado.**\n\n*Detalhes: {e}*"
                st.error(api_answer)
        
        # Adiciona a resposta final (seja de sucesso ou de erro) ao histórico de mensagens.
        st.session_state.messages.append({"role": "assistant", "content": api_answer})