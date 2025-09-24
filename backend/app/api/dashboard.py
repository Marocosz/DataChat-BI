# =============================================================================
# API ROUTER PARA O DASHBOARD COM CONNECTION POOLING
# =============================================================================

import logging
import psycopg2
# --- INÍCIO DA ATUALIZAÇÃO 1: Importar o Pool ---
from psycopg2.pool import SimpleConnectionPool
# ----------------------------------------------
from fastapi import APIRouter, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# --- INÍCIO DA ATUALIZAÇÃO 2: Criar o Pool de Conexões ---
# Criamos o pool de conexões UMA VEZ, quando o módulo é carregado.
# Isso evita o custo de criar conexões novas a cada requisição.
try:
    connection_pool = SimpleConnectionPool(
        minconn=1,  # Número mínimo de conexões a manter abertas
        maxconn=5,  # Número máximo de conexões a serem abertas
        host=settings.DB_HOST,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        port=settings.DB_PORT
    )
    logger.info("Pool de conexões com o banco de dados do dashboard criado com sucesso.")
except Exception as e:
    logger.error(f"Falha ao criar o pool de conexões do dashboard: {e}")
    connection_pool = None # Garante que a app possa iniciar mesmo com erro no DB
# ---------------------------------------------------------

# --- ATUALIZAÇÃO 3: A função antiga get_db_conn() foi REMOVIDA ---
# Agora cada endpoint gerencia sua própria conexão do pool.

@router.get("/kpis")
def get_dashboard_kpis():
    """
    Retorna os KPIs. Agora usa uma conexão do pool.
    """
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
    conn = None # Inicializa a conexão como None
    try:
        # Pega uma conexão "emprestada" do pool
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(sql)
            kpis = cur.fetchone()
            if kpis:
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
        # O bloco 'finally' garante que a conexão SEMPRE será devolvida ao pool,
        # mesmo que ocorra um erro. Isso é CRUCIAL para não vazar conexões.
        if conn:
            connection_pool.putconn(conn)

@router.get("/operacoes_por_status")
def get_operacoes_por_status():
    if not connection_pool:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço de banco de dados indisponível.")
        
    sql = "SELECT status, COUNT(*) as count FROM operacoes_logisticas GROUP BY status ORDER BY count DESC;"
    conn = None
    try:
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(sql)
            data = cur.fetchall()
            return [{"name": str(row[0]), "value": row[1]} for row in data]
    finally:
        if conn:
            connection_pool.putconn(conn)

@router.get("/valor_frete_por_uf")
def get_valor_frete_por_uf():
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
            return [{"name": row[0].strftime('%d/%m'), "value": row[1]} for row in data]
    finally:
        if conn:
            connection_pool.putconn(conn)

@router.get("/top_clientes_por_valor")
def get_top_clientes_por_valor():
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