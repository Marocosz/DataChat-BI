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

    # Nomes dos modelos Groq (carregados do .env)
    GROQ_SQL_MODEL: str
    GROQ_ANSWER_MODEL: str

    # Credenciais do Banco de Dados
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_PORT: int = 5432

    @property
    def DATABASE_URI(self) -> str:
        """Gera a URI de conexão para o SQLAlchemy/LangChain."""
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Instância única que será importada por outros módulos
settings = Settings()