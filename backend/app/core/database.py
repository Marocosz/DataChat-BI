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
    Gera uma string de schema muito compacta para ser enviada no prompt
    
    Esta função se conecta diretamente ao banco, busca os metadados das colunas
    e formata um texto simples e legível para a IA.
    
    Exemplo saída:
        Tabela: clientes
        Colunas: id (integer), nome_razao_social (character varying), cnpj_cpf (character varying), email_contato (character varying), telefone_contato (character varying), data_cadastro (timestamp with time zone)

        Tabela: operacoes_logisticas
        Colunas: id (bigint), codigo_operacao (character varying), tipo (tipo_operacao_logistica), status (status_operacao), cliente_id (integer), data_emissao (timestamp with time zone), data_previsao_entrega (date), data_entrega_realizada (timestamp with time zone), uf_coleta (character varying), cidade_coleta (character varying), uf_destino (character varying), cidade_destino (character varying), peso_kg (numeric), quantidade_volumes (integer), valor_mercadoria (numeric), natureza_carga (character varying), valor_frete (numeric), valor_seguro (numeric), codigo_rastreio (character varying), observacoes (text)
    """
    conn = None
    try:
        logger.info("Gerando schema compacto do banco de dados.")
        # Conecta-se diretamente ao PostgreSQL usando psycopg2 e nossas configurações.
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
        
        # Itera sobre cada tabela para buscar suas colunas.
        for table in tables:
            # Executa uma query no 'information_schema', que é um banco de dados de metadados padrão do SQL.
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            # Usa "list comprehension" para formatar cada linha de resultado em "nome_coluna (tipo_dado)".
            columns = [f"{row[0]} ({row[1]})" for row in cur.fetchall()]
            
            # Monta a string final para esta tabela e a adiciona à lista.
            schema_parts.append(f"Tabela: {table}\nColunas: {', '.join(columns)}")
            
        cur.close()
        logger.info("Schema compacto gerado com sucesso.")
        
        # Junta as partes do schema com duas quebras de linha para melhor formatação.
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