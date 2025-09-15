# ingest.py
import os
from langchain_community.document_loaders import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Caminho para o seu JSON e para o banco de vetores que será criado
JSON_PATH = "backend/data/dados_completos.json"
CHROMA_DB_PATH = "chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def main():
    print("Iniciando o processo de ingestão de metadados...")

    # 1. Carregar os dados do JSON
    print(f"Carregando o arquivo JSON de: {JSON_PATH}")
    loader = JSONLoader(
        file_path=JSON_PATH,
        jq_schema='.', # Carrega o JSON inteiro
        text_content=False # Garante que todo o conteúdo seja processado
    )
    documents = loader.load()
    print(f"Carregado {len(documents)} documentos do JSON.")

    # 2. Dividir os documentos em pedaços menores (chunks)
    # Isso melhora a precisão da busca por similaridade
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    print(f"Documentos divididos em {len(texts)} chunks de texto.")

    # 3. Inicializar o modelo de embedding
    # Este modelo roda localmente e transforma os chunks de texto em vetores
    print(f"Carregando o modelo de embedding: {EMBEDDING_MODEL_NAME}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # 4. Criar e persistir o banco de dados de vetores
    print(f"Criando e salvando o banco de dados Chroma em: {CHROMA_DB_PATH}")
    # Esta linha cria o banco de dados a partir dos textos e dos vetores e o salva no disco
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    
    print("\n--- Ingestão Concluída com Sucesso! ---")
    print(f"O banco de vetores foi criado na pasta '{CHROMA_DB_PATH}'.")

if __name__ == "__main__":
    main()