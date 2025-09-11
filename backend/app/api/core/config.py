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