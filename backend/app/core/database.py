# =============================================================================
# ARQUIVO DE GERENCIAMENTO DO BANCO DE DADOS
#
# Este módulo centraliza toda a interação com o banco de dados PostgreSQL.
# Ele é responsável por:
# 1. Criar uma instância de conexão que o LangChain pode usar para EXECUTAR queries.
# 2. Gerar uma representação de texto compacta do schema do banco para ser
#    enviada como CONTEXTO para o LLM, evitando erros de requisição muito grande.
# =============================================================================

# --- Bloco de Importações ---
import logging # Importa a biblioteca de logging para registrar informações e erros.
import psycopg2
from langchain_community.utilities import SQLDatabase
from .config import settings

# --- Instanciação do Logger ---
# Obtém um logger específico para este módulo, o que ajuda a identificar a origem das mensagens de log.
logger = logging.getLogger(__name__)

def get_db_connection() -> SQLDatabase:
    """
    Cria a conexão principal do LangChain, que será usada para EXECUTAR as queries SQL
    geradas pela IA.
    """
    try:
        # Usa um método do LangChain para criar a conexão a partir da URI que montamos no config.py.
        db = SQLDatabase.from_uri(
            settings.DATABASE_URI,
            # Limita as tabelas que o LangChain "enxerga", por segurança e para manter o foco.
            include_tables=['operacoes_logisticas', 'clientes'],
            # Definimos como 0 para não incluir nenhuma linha de exemplo, reduzindo o tamanho do schema.
            sample_rows_in_table_info=0
        )
        
        logger.info("Conexão com o banco de dados (LangChain) estabelecida com sucesso.")
        return db
    
    except Exception as e:
        logger.error(f"Falha ao conectar com o banco de dados (LangChain): {e}")
        raise

def get_compact_db_schema() -> str:
    """
    Gera uma string de schema muito compacta, incluindo os valores
    possíveis para os tipos ENUM, para guiar melhor a IA.
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
            columns = []
            for row in cur.fetchall():
                column_name, data_type = row
                # --- LÓGICA ADICIONADA PARA ENUMs ---
                # Se o tipo da coluna for um dos nossos ENUMs customizados...
                if data_type in ['tipo_operacao_logistica', 'status_operacao']:
                    # ...busca os valores possíveis para esse ENUM.
                    cur.execute(f"SELECT unnest(enum_range(NULL::{data_type}))::text")
                    enum_values = [f"'{val[0]}'" for val in cur.fetchall()]
                    # E adiciona essa informação à descrição da coluna.
                    columns.append(f"{column_name} ({data_type}, valores possíveis: {', '.join(enum_values)})")
                else:
                    columns.append(f"{column_name} ({data_type})")
                # ------------------------------------

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

# --- Instanciação da Conexão ---
# Cria uma instância única da conexão do LangChain quando a aplicação é iniciada.
db_instance = get_db_connection()