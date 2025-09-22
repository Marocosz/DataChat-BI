# app/core/database.py (Versão com schema compacto)
import logging
import psycopg2
from langchain_community.utilities import SQLDatabase
from .config import settings

logger = logging.getLogger(__name__)

def get_db_connection() -> SQLDatabase:
    """
    Cria a conexão principal do LangChain. Não usaremos mais o .table_info daqui
    para o prompt principal, para evitar o erro 413.
    """
    try:
        db = SQLDatabase.from_uri(
            settings.DATABASE_URI,
            include_tables=['operacoes_logisticas', 'clientes'],
            sample_rows_in_table_info=0
        )
        logger.info("Conexão com o banco de dados estabelecida com sucesso.")
        return db
    except Exception as e:
        logger.error(f"Falha ao conectar com o banco de dados: {e}")
        raise

def get_compact_db_schema() -> str:
    """
    Gera uma string de schema muito compacta para ser enviada no prompt,
    evitando o erro 'Request Entity Too Large'.
    """
    conn = None
    try:
        logger.info("Gerando schema compacto do banco de dados.")
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASS,
            port=settings.DB_PORT
        )
        cur = conn.cursor()
        
        schema_parts = []
        tables = ['clientes', 'operacoes_logisticas']
        
        for table in tables:
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            columns = [f"{row[0]} ({row[1]})" for row in cur.fetchall()]
            schema_parts.append(f"Tabela: {table}\nColunas: {', '.join(columns)}")
            
        cur.close()
        logger.info("Schema compacto gerado com sucesso.")
        return "\n\n".join(schema_parts)
    except Exception as e:
        logger.error(f"Erro ao gerar schema compacto: {e}")
        return "Erro ao obter schema do banco de dados."
    finally:
        if conn:
            conn.close()

db_instance = get_db_connection()