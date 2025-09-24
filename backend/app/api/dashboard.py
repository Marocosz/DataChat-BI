# =============================================================================
# API ROUTER PARA O DASHBOARD COM CONNECTION POOLING
#
# Este arquivo implementa os endpoints da API para o dashboard, utilizando o framework
# FastAPI. O principal objetivo é fornecer dados analíticos de forma eficiente e segura
# a partir do banco de dados PostgreSQL, empregando a técnica de Connection Pooling.
#
# O Connection Pooling é uma técnica crucial para o desempenho. Em vez de criar e fechar
# uma nova conexão para cada requisição (o que é lento e custoso), um "pool" de conexões
# é mantido aberto. As requisições pegam uma conexão "emprestada", a usam, e a devolvem
# ao pool, reduzindo a latência e a carga sobre o banco de dados, e prevenindo o "vazamento"
# de conexões.
# =============================================================================

import logging
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from fastapi import APIRouter, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Cria o pool de conexões com o banco de dados.
# Isso é feito apenas UMA VEZ, na inicialização da aplicação,
# garantindo que o pool esteja pronto para ser usado por todas as requisições.
try:
    connection_pool = SimpleConnectionPool(
        minconn=1,  # Número mínimo de conexões a manter abertas.
        maxconn=5,  # Número máximo de conexões que podem ser abertas sob demanda.
        host=settings.DB_HOST,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        port=settings.DB_PORT
    )
    logger.info("Pool de conexões com o banco de dados do dashboard criado com sucesso.")
except Exception as e:
    logger.error(f"Falha ao criar o pool de conexões do dashboard: {e}")
    # Define o pool como None para que os endpoints saibam que o serviço não está disponível.
    connection_pool = None

# Agora, cada endpoint usa uma conexão do pool.
@router.get("/kpis")
def get_dashboard_kpis():
    """
    Retorna os principais KPIs do dashboard, como o total de operações e valores.
    """
    # Verifica se o pool de conexões foi inicializado com sucesso.
    if not connection_pool:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de banco de dados indisponível."
        )

    sql = """
    SELECT
        COUNT(*) AS total_operacoes,
        SUM(CASE WHEN status = 'ENTREGUE' THEN 1 ELSE 0 END) AS operacoes_entregues,
        SUM(CASE WHEN status = 'EM_TRANSITO' THEN 1 ELSE 0 END) AS operacoes_em_transito,
        SUM(valor_mercadoria) AS valor_total_mercadorias
    FROM operacoes_logisticas;
    """
    conn = None  # Inicializa a variável de conexão.
    try:
        # Pega uma conexão disponível do pool.
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(sql)
            kpis = cur.fetchone()
            if kpis:
                # Retorna os dados como um dicionário.
                return {
                    "total_operacoes": kpis[0],
                    "operacoes_entregues": kpis[1],
                    "operacoes_em_transito": kpis[2],
                    "valor_total_mercadorias": float(kpis[3]) if kpis[3] else 0
                }
            return {}
    except Exception as e:
        logger.error(f"Erro ao buscar KPIs do dashboard: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar dados do dashboard.")
    finally:
        # CRUCIAL: Este bloco garante que a conexão será devolvida ao pool,
        # mesmo se ocorrer uma exceção. Isso evita que as conexões sejam exauridas.
        if conn:
            connection_pool.putconn(conn)

@router.get("/operacoes_por_status")
def get_operacoes_por_status():
    """
    Retorna a contagem de operações agrupadas por status.
    """
    if not connection_pool:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço de banco de dados indisponível.")
        
    sql = "SELECT status, COUNT(*) as count FROM operacoes_logisticas GROUP BY status ORDER BY count DESC;"
    conn = None
    try:
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(sql)
            data = cur.fetchall()
            # Converte a lista de tuplas em uma lista de dicionários para a resposta JSON.
            return [{"name": str(row[0]), "value": row[1]} for row in data]
    finally:
        if conn:
            connection_pool.putconn(conn)

@router.get("/valor_frete_por_uf")
def get_valor_frete_por_uf():
    """
    Retorna o valor total de frete por estado de destino.
    """
    if not connection_pool:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço de banco de dados indisponível.")
        
    sql = """
        SELECT uf_destino, SUM(valor_frete) as total_frete
        FROM operacoes_logisticas
        WHERE valor_frete IS NOT NULL
        GROUP BY uf_destino
        ORDER BY total_frete DESC
        LIMIT 10;
    """
    conn = None
    try:
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(sql)
            data = cur.fetchall()
            return [{"name": row[0], "value": float(row[1])} for row in data]
    finally:
        if conn:
            connection_pool.putconn(conn)

@router.get("/operacoes_por_dia")
def get_operacoes_por_dia():
    """
    Retorna a contagem de operações por dia nos últimos 30 dias.
    """
    if not connection_pool:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço de banco de dados indisponível.")
        
    sql = """
        SELECT CAST(data_emissao AS DATE) as dia, COUNT(*) as count
        FROM operacoes_logisticas
        WHERE data_emissao >= NOW() - INTERVAL '30 days'
        GROUP BY dia
        ORDER BY dia ASC;
    """
    conn = None
    try:
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(sql)
            data = cur.fetchall()
            # Formata a data para um formato mais amigável para o front-end.
            return [{"name": row[0].strftime('%d/%m'), "value": row[1]} for row in data]
    finally:
        if conn:
            connection_pool.putconn(conn)

@router.get("/top_clientes_por_valor")
def get_top_clientes_por_valor():
    """
    Retorna os 5 clientes com o maior valor total de mercadorias.
    """
    if not connection_pool:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço de banco de dados indisponível.")
        
    sql = """
        SELECT
            c.nome_razao_social,
            SUM(o.valor_mercadoria) as total_valor
        FROM operacoes_logisticas o
        JOIN clientes c ON o.cliente_id = c.id
        WHERE o.valor_mercadoria IS NOT NULL
        GROUP BY c.nome_razao_social
        ORDER BY total_valor DESC
        LIMIT 5;
    """
    conn = None
    try:
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(sql)
            data = cur.fetchall()
            return [{"name": row[0], "value": float(row[1])} for row in data]
    finally:
        if conn:
            connection_pool.putconn(conn)