# frontend/app.py
import streamlit as st
import requests

API_URL = "http://localhost:8000/api/v1/chat/query"

st.set_page_config(page_title="Assistente de Catálogo de Dados", page_icon="🧠", layout="wide")
st.title("🧠 Assistente de Catálogo de Dados")
st.caption("Pergunte-me sobre esquemas, tabelas e colunas do nosso banco de dados!")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou seu assistente para explorar nosso catálogo de dados. O que você gostaria de saber?"}]
if "session_id" not in st.session_state:
    st.session_state.session_id = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("O que significa a coluna CD_CLIENTE_LEGADO?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analisando metadados..."):
            try:
                payload = {"query": prompt, "session_id": st.session_state.session_id}
                response = requests.post(API_URL, json=payload)
                response.raise_for_status()
                
                api_data = response.json()
                api_answer = api_data["answer"]
                st.session_state.session_id = api_data["session_id"]
                
                st.markdown(api_answer)
            except Exception as e:
                api_answer = f"Ocorreu um erro ao processar sua requisição: {e}"
                st.error(api_answer)
    
    st.session_state.messages.append({"role": "assistant", "content": api_answer})