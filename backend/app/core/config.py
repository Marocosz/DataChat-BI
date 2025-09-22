# =============================================================================
# ARQUIVO DE CONFIGURAÇÃO CENTRALIZADA (SETTINGS)
#
# Este arquivo funciona como o "painel de controle" da nossa aplicação.
# Ele é responsável por carregar, validar e centralizar todas as 
# configurações externas, como chaves de API e credenciais de banco de dados,
# a partir do arquivo .env.
#
# Usamos a biblioteca Pydantic para garantir que as configurações não apenas
# sejam carregadas, mas também que tenham o tipo de dado correto (texto, número, etc.),
# evitando erros em outras partes do sistema.
# =============================================================================

from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Definição da Classe de Configurações ---
# Criamos uma classe que herda de BaseSettings. O Pydantic irá automaticamente
# tentar preencher os atributos desta classe com variáveis de ambiente de mesmo nome.
class Settings(BaseSettings):
    """
    Gerencia as configurações da aplicação, carregando variáveis do arquivo .env.
    """
    
    # Configura como o Pydantic deve se comportar ao carregar as configurações.
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # --- Definição dos Atributos de Configuração ---

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
    # Define um valor padrão para DB_PORT. Se não for encontrado no .env, usará 5432.
    DB_PORT: int = 5432

    # --- Propriedade Computada ---
    # O decorador @property nos permite criar um "atributo dinâmico" que é gerado a partir de outros.
    @property
    def DATABASE_URI(self) -> str:
        """Gera a URI de conexão para o SQLAlchemy/LangChain."""
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# --- Instanciação do Objeto de Configurações ---
# Esta é a linha que efetivamente executa tudo. Ela cria uma instância única da classe Settings.
settings = Settings()