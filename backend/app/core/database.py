# app/core/database.py (Versão Final Corrigida)
import logging
from langchain_community.utilities import SQLDatabase
from .config import settings

# Configura um logger para este módulo
logger = logging.getLogger(__name__)

def get_db_connection() -> SQLDatabase:
    """
    Cria e retorna uma conexão de banco de dados gerenciada pelo LangChain.
    """
    try:
        db = SQLDatabase.from_uri(
            settings.DATABASE_URI,
            include_tables=['operacoes_logisticas', 'clientes'],
            # ALTERAÇÃO PRINCIPAL AQUI:
            # Não vamos mais incluir linhas de exemplo para manter o prompt compacto.
            sample_rows_in_table_info=0 
        )
        logger.info("Conexão com o banco de dados estabelecida com sucesso.")
        return db
    except Exception as e:
        logger.error(f"Falha ao conectar com o banco de dados: {e}")
        raise

db_instance = get_db_connection()