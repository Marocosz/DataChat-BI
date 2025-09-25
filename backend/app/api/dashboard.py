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

# =============================================================================
# API ROUTER PARA O DASHBOARD - VERSÃO FINAL E ROBUSTA
# Padrões aplicados: Connection Pooling, Cache e Dependency Injection.
# =============================================================================
# =============================================================================
# API ROUTER PARA O DASHBOARD - VERSÃO FINAL COM DEBUG DE KPIs
# =============================================================================

# =============================================================================
# API ROUTER PARA O DASHBOARD - VERSÃO FINAL E DEFINITIVA
# Padrões aplicados: Connection Pooling, Cache e Dependency Injection com RealDictCursor.
# =============================================================================

# =============================================================================
# API ROUTER PARA O DASHBOARD - VERSÃO FINAL E UNIFICADA
# Padrões aplicados: Connection Pooling, Cache, Dependency Injection com RealDictCursor.
# =============================================================================

# =============================================================================
# API ROUTER PARA O DASHBOARD - VERSÃO FINAL E DEFINITIVA
# Padrões: Connection Pooling, Cache, Dependency Injection com RealDictCursor.
# =============================================================================

import logging
import psycopg2
import psycopg2.extras # Para retornar dicionários em vez de tuplas
from psycopg2.pool import SimpleConnectionPool
from fastapi import APIRouter, HTTPException, status, Depends
from app.core.config import settings
from cachetools import cached, TTLCache

logger = logging.getLogger(__name__)
router = APIRouter()

# --- 1. POOL DE CONEXÕES ---
# Criado uma única vez para ser reutilizado por toda a aplicação.
try:
    connection_pool = SimpleConnectionPool(
        minconn=1, maxconn=10,
        host=settings.DB_HOST, dbname=settings.DB_NAME,
        user=settings.DB_USER, password=settings.DB_PASS, port=settings.DB_PORT
    )
    logger.info("Pool de conexões do dashboard criado com sucesso.")
except Exception as e:
    logger.error(f"Falha ao criar o pool de conexões do dashboard: {e}", exc_info=True)
    connection_pool = None

# --- 2. CACHE ---
# Cache em memória com 5 minutos de validade para os resultados.
cache = TTLCache(maxsize=10, ttl=300)

# --- 3. DEPENDÊNCIA DO FASTAPI ---
# Esta função gerencia o ciclo de vida da conexão de forma segura e elegante.
# Ela "empresta" uma conexão do pool, a entrega para o endpoint,
# e garante que ela seja devolvida ao pool no final, mesmo se ocorrer um erro.
def get_db_cursor():
    if not connection_pool:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço de banco de dados indisponível.")
    conn = None
    try:
        conn = connection_pool.getconn()
        # Usamos um cursor que retorna dicionários, o que deixa o código mais limpo.
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            yield cursor
    finally:
        if conn:
            connection_pool.putconn(conn)

# --- 4. ENDPOINTS ---
# Cada endpoint agora é simples: recebe o cursor, executa a query e retorna o resultado.

@router.get("/kpis")
@cached(cache)
def get_dashboard_kpis(cur = Depends(get_db_cursor)):
    logger.info("Buscando KPIs do banco (CACHE MISS)...")
    sql = "SELECT COUNT(*) as total_operacoes, SUM(CASE WHEN status = 'ENTREGUE' THEN 1 ELSE 0 END) as operacoes_entregues, SUM(CASE WHEN status = 'EM_TRANSITO' THEN 1 ELSE 0 END) as operacoes_em_transito, SUM(valor_mercadoria) as valor_total_mercadorias FROM operacoes_logisticas;"
    try:
        cur.execute(sql)
        kpis = cur.fetchone()
        if kpis and kpis.get('valor_total_mercadorias'):
            kpis['valor_total_mercadorias'] = float(kpis['valor_total_mercadorias'])
        return kpis or {}
    except Exception as e:
        logger.error(f"Erro ao buscar KPIs do dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar KPIs.")

@router.get("/operacoes_por_status")
@cached(cache)
def get_operacoes_por_status(cur = Depends(get_db_cursor)):
    logger.info("Buscando operações por status do banco (CACHE MISS)...")
    sql = "SELECT status as name, COUNT(*) as value FROM operacoes_logisticas GROUP BY status ORDER BY value DESC;"
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        logger.error(f"Erro ao buscar operações por status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar operações por status.")

@router.get("/valor_frete_por_uf")
@cached(cache)
def get_valor_frete_por_uf(cur = Depends(get_db_cursor)):
    logger.info("Buscando valor de frete por UF do banco (CACHE MISS)...")
    sql = "SELECT uf_destino as name, SUM(valor_frete) as value FROM operacoes_logisticas WHERE valor_frete IS NOT NULL GROUP BY name ORDER BY value DESC LIMIT 10;"
    try:
        cur.execute(sql)
        data = cur.fetchall()
        for row in data:
            if row.get('value'): row['value'] = float(row['value'])
        return data
    except Exception as e:
        logger.error(f"Erro ao buscar valor de frete por UF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar valor de frete por UF.")

@router.get("/operacoes_por_dia")
@cached(cache)
def get_operacoes_por_dia(cur = Depends(get_db_cursor)):
    logger.info("Buscando operações por dia do banco (CACHE MISS)...")
    sql = "SELECT CAST(data_emissao AS DATE) as name, COUNT(*) as value FROM operacoes_logisticas WHERE data_emissao >= NOW() - INTERVAL '30 days' GROUP BY name ORDER BY name ASC;"
    try:
        cur.execute(sql)
        data = cur.fetchall()
        for row in data:
            if row.get('name'): row['name'] = row['name'].strftime('%d/%m')
        return data
    except Exception as e:
        logger.error(f"Erro ao buscar operações por dia: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar operações por dia.")

@router.get("/top_clientes_por_valor")
@cached(cache)
def get_top_clientes_por_valor(cur = Depends(get_db_cursor)):
    logger.info("Buscando top clientes do banco (CACHE MISS)...")
    sql = "SELECT c.nome_razao_social as name, SUM(o.valor_mercadoria) as value FROM operacoes_logisticas o JOIN clientes c ON o.cliente_id = c.id WHERE o.valor_mercadoria IS NOT NULL GROUP BY name ORDER BY value DESC LIMIT 5;"
    try:
        cur.execute(sql)
        data = cur.fetchall()
        for row in data:
            if row.get('value'): row['value'] = float(row['value'])
        return data
    except Exception as e:
        logger.error(f"Erro ao buscar top clientes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar top clientes.")