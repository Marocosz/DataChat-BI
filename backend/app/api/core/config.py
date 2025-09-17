# backend/app/api/core/config.py

"""
Este módulo é responsável pelo gerenciamento centralizado das configurações da aplicação.
Ele utiliza a biblioteca `pydantic-settings` para criar um objeto de configuração fortemente tipado.

Seu principal objetivo é carregar, validar e expor variáveis de ambiente de forma segura e organizada.
Isso evita que informações sensíveis (como chaves de API) ou configurações de ambiente (como caminhos de
banco de dados) sejam 'hardcoded' (escritas diretamente) no código-fonte, o que é uma má prática de
segurança e manutenção.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Classe de configurações para carregar variáveis de ambiente.
    """
    # Chave da API para o provedor de LLM (agora Groq)
    GROQ_API_KEY: str

    # Caminho de conexão (URI) para o banco de dados
    DATABASE_URI: str

    # Configuração para Pydantic ler as variáveis a partir de um arquivo .env
    model_config = SettingsConfigDict(env_file=".env")

# Cria uma instância única das configurações para ser usada em toda a aplicação
settings = Settings()