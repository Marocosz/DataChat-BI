# app/main.py
from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(
    title="Catálogo SUPP Bot API (Groq Edition)",
    description="API para interagir com um chatbot que consulta o banco de dados do catálogo, com a velocidade do Groq.",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Bem-vindo à API do Catálogo SUPP Bot!"}