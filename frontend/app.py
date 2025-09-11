# frontend/app.py
import streamlit as st
import requests
import time

# --- Configurações da Página ---
st.set_page_config(
    page_title="Chat com Catálogo",
    page_icon="🤖",
    layout="centered"
)

# --- Configurações da API ---
# URL do nosso backend FastAPI
API_URL = "http://localhost:8000/api/v1/chat/query"

# --- Título e Cabeçalho ---
st.title("🤖 Chat com Catálogo SUPP")
st.caption("Faça perguntas sobre nosso catálogo de produtos e eu responderei!")

# --- Gerenciamento do Histórico da Conversa ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Como posso ajudar com nosso catálogo de produtos hoje?"}
    ]

# --- Exibição do Histórico de Chat ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Input do Usuário e Lógica de Comunicação ---
if prompt := st.chat_input("Qual a sua pergunta?"):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = requests.post(API_URL, json={"query": prompt})
                response.raise_for_status() 

                api_answer = response.json()["answer"]

                full_response = ""
                message_placeholder = st.empty()
                # Simula o efeito de digitação para uma melhor UX
                for chunk in api_answer.split():
                    full_response += chunk + " "
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)

            except requests.exceptions.RequestException as e:
                full_response = f"Desculpe, não consegui me conectar ao meu cérebro. Verifique se a API backend está rodando. Erro: {e}"
                st.error(full_response)

            except Exception as e:
                full_response = f"Ocorreu um erro inesperado: {e}"
                st.error(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})