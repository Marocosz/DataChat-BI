# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Gerencia as configurações da aplicação, carregando variáveis do arquivo .env.
    """
    # Carrega o arquivo .env
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # Credenciais do Groq
    GROQ_API_KEY: str

    # Credenciais do Banco de Dados
    DB_HOST: str
    DB_DATABASE: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_PORT: int = 5432

    @property
    def DATABASE_URI(self) -> str:
        """Gera a URI de conexão para o SQLAlchemy/LangChain."""
        return f"postgresql+psycopg2://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"

# Instância única que será importada por outros módulos
settings = Settings()