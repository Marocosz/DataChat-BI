# =============================================================================
# ARQUIVO DE GERENCIAMENTO DO BANCO DE DADOS
#
# Este módulo centraliza toda a interação com o banco de dados PostgreSQL.
# Ele é responsável por:
# 1. Criar uma instância de conexão que o LangChain pode usar para EXECUTAR queries.
# 2. Gerar uma representação de texto compacta do schema do banco para ser
#    enviada como CONTEXTO para o LLM, evitando erros de requisição muito grande.
# =============================================================================

import logging
import psycopg2
from langchain_community.utilities import SQLDatabase
# Necessário para criar a engine e usar variáveis separadas.
from sqlalchemy import create_engine 
from .config import settings

# Obtém um logger específico para este módulo.
logger = logging.getLogger(__name__)

# Variável global para armazenar o schema em cache, evitando múltiplas chamadas ao DB.
_cached_schema: str | None = None

def get_db_connection() -> SQLDatabase:
    """
    Cria a conexão principal do LangChain, que será usada para EXECUTAR as queries SQL
    geradas pela IA.
    
    Esta função foi modificada para montar a URI a partir das variáveis separadas do .env
    e adicionar o parâmetro SSL obrigatório via connect_args.

    Returns:
        Uma instância de SQLDatabase configurada para o banco de dados do projeto.
    
    Raises:
        Exception: Se a conexão com o banco de dados falhar.
    """
    
    # 1. Monta a URI completa a partir das variáveis do .env
    DATABASE_URI_FULL = (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    # 2. Argumento necessário para conexão SSL/TLS com serviços em nuvem como Render
    SSL_ARGS = {"sslmode": "require"}
    
    try:
        # 3. Criamos a Engine explicitamente, passando os argumentos de conexão (SSL)
        engine = create_engine(
            DATABASE_URI_FULL,
            connect_args=SSL_ARGS
        )
        
        # 4. Criamos a instância SQLDatabase do LangChain usando a Engine customizada.
        db = SQLDatabase(
            engine=engine,
            include_tables=['operacoes_logisticas', 'clientes'],
            sample_rows_in_table_info=0
        )
        
        logger.info("Conexão com o banco de dados (LangChain) estabelecida com sucesso.")
        return db
    
    except Exception as e:
        logger.error(f"Falha ao conectar com o banco de dados (LangChain): {e}")
        raise

def _generate_compact_db_schema() -> str:
    """
    Gera uma string de schema muito compacta, incluindo os valores
    possíveis para os tipos ENUM, para guiar melhor a IA.
    Esta função se conecta ao banco e faz o trabalho pesado.

    Returns:
        Uma string formatada com o esquema do banco de dados.
    """
    conn = None
    try:
        logger.info("Gerando schema compacto do banco de dados a partir do DB...")
        
        # ADIÇÃO DO PARÂMETRO SSL AQUI: Resolve erro SSL/TLS no psycopg2 direto.
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASS,
            port=settings.DB_PORT,
            sslmode='require' # <--- A correção de segurança
        )
        cur = conn.cursor()
        
        schema_parts = []
        tables = ['clientes', 'operacoes_logisticas']
        
        for table in tables:
            # Consulta as colunas e tipos de dados de cada tabela.
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            columns = []
            for row in cur.fetchall():
                column_name, data_type = row
                # Para colunas ENUM, busca os valores possíveis para adicionar ao schema.
                if data_type in ['tipo_operacao_logistica', 'status_operacao']:
                    cur.execute(f"SELECT unnest(enum_range(NULL::{data_type}))::text")
                    enum_values = [f"'{val[0]}'" for val in cur.fetchall()]
                    columns.append(f"{column_name} ({data_type}, valores possíveis: {', '.join(enum_values)})")
                else:
                    columns.append(f"{column_name} ({data_type})")

            schema_parts.append(f"Tabela: {table}\nColunas: {', '.join(columns)}")
            
        cur.close()
        logger.info("Schema compacto gerado com sucesso.")
        return "\n\n".join(schema_parts)
    except Exception as e:
        logger.error(f"Erro ao gerar schema compacto: {e}")
        return "Erro ao obter schema do banco de dados."
    finally:
        # Fecha a conexão direta para liberar recursos.
        if conn:
            conn.close()

def get_compact_db_schema() -> str:
    """
    Função pública que retorna o schema do banco de dados.
    Ela utiliza um sistema de cache para evitar múltiplas chamadas ao banco,
    gerando o schema apenas na primeira vez que é solicitado.

    Returns:
        A string contendo o esquema do banco de dados.
    """
    global _cached_schema
    # Se o cache estiver vazio, chama a função geradora.
    if _cached_schema is None:
        _cached_schema = _generate_compact_db_schema()
    
    # Retorna o schema que está em cache.
    return _cached_schema

# Cria uma instância única da conexão do LangChain quando a aplicação é iniciada.
# Esta linha tentará se conectar ao banco imediatamente, levantando um erro se falhar.
db_instance = get_db_connection()