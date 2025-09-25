# =============================================================================
# API ROUTER PARA O DASHBOARD

# Este arquivo contém os endpoints da API para o dashboard.
# Padrões de arquitetura aplicados:
# 1. Connection Pooling: Para reutilizar conexões com o banco de dados e melhorar a performance.
# 2. Cache: Para armazenar em memória os resultados de queries lentas, tornando recargas rápidas.
# 3. Dependency Injection: Padrão do FastAPI para gerenciar recursos (como conexões) de forma segura.
# =============================================================================

# --- Bloco de Importações ---
import logging
import psycopg2
import psycopg2.extras  # Importa funcionalidades extras, como o RealDictCursor
from psycopg2.pool import SimpleConnectionPool # A classe para o pool de conexões
from fastapi import APIRouter, HTTPException, status, Depends # Componentes do FastAPI
from app.core.config import settings # Nossas configurações (URL do banco, etc.)
from cachetools import cached, TTLCache # A biblioteca para o cache em memória

# --- Configuração Inicial ---
# Configura um logger para este arquivo, para podermos ver mensagens no terminal.
logger = logging.getLogger(__name__)
# Cria um "roteador", um mini-aplicativo para agrupar todos os endpoints do dashboard.
router = APIRouter()

# --- 1. POOL DE CONEXÕES ---
# O pool é criado UMA ÚNICA VEZ quando a aplicação inicia.
try:
    connection_pool = SimpleConnectionPool(
        minconn=1,       # Manter pelo menos 1 conexão sempre aberta e pronta para uso.
        maxconn=10,      # Permitir no máximo 10 conexões simultâneas para não sobrecarregar o banco.
        host=settings.DB_HOST,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        port=settings.DB_PORT
    )
    logger.info("Pool de conexões do dashboard criado com sucesso.")
except Exception as e:
    # Se a conexão com o banco falhar na inicialização, logamos o erro.
    logger.error(f"Falha ao criar o pool de conexões do dashboard: {e}", exc_info=True)
    connection_pool = None

# --- 2. CACHE ---
# O cache também é criado UMA ÚNICA VEZ.
# TTLCache: "Time To Live" Cache, onde cada item tem um tempo de vida.
cache = TTLCache(
    maxsize=10,  # O cache armazenará no máximo 10 resultados diferentes.
    ttl=300      # ttl (Time To Live) = 300 segundos (5 minutos). Após 5 min, o dado é considerado "velho" e será buscado novamente no banco.
)

# --- 3. DEPENDÊNCIA DO FASTAPI PARA GERENCIAR CONEXÕES ---
# Esta função é a peça central que conecta o Pool com os Endpoints.
def get_db_cursor():
    # Verifica se o pool foi criado com sucesso na inicialização.
    if not connection_pool:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço de banco de dados indisponível.")
    
    conn = None # Inicializa a variável de conexão
    try:
        # Pega uma conexão "emprestada" do pool. Se não houver nenhuma disponível, espera por uma.
        conn = connection_pool.getconn()
        
        # O `yield` é a mágica da injeção de dependência: ele "entrega" o cursor para a função do endpoint
        # e pausa a execução desta função aqui.
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            yield cursor
            
    finally:
        # Quando o endpoint termina (com sucesso ou erro), a execução desta função continua após o `yield`.
        # O bloco `finally` GARANTE que a conexão SEMPRE será devolvida ao pool, evitando vazamentos.
        if conn:
            connection_pool.putconn(conn)

# --- 4. ENDPOINTS ---
# Cada endpoint agora usa a estrutura:
# @cached(cache): Aplica o cache. Se o resultado estiver na memória, retorna-o imediatamente sem executar a função.
# Depends(get_db_cursor): Recebe um cursor pronto para uso da função de dependência.

@router.get("/kpis")
@cached(cache)
def get_dashboard_kpis(cur = Depends(get_db_cursor)):
    # Esta mensagem só aparecerá no log se o resultado não estiver no cache.
    logger.info("Buscando KPIs do banco (CACHE MISS)...")
    sql = "SELECT COUNT(*) as total_operacoes, SUM(CASE WHEN status = 'ENTREGUE' THEN 1 ELSE 0 END) as operacoes_entregues, SUM(CASE WHEN status = 'EM_TRANSITO' THEN 1 ELSE 0 END) as operacoes_em_transito, SUM(valor_mercadoria) as valor_total_mercadorias FROM operacoes_logisticas;"
    try:
        cur.execute(sql)
        kpis = cur.fetchone() # Pega a única linha de resultado. `kpis` será um dicionário.
        
        # O banco retorna o tipo 'Decimal' para somas, que não é compatível com JSON. Convertemos para float.
        if kpis and kpis.get('valor_total_mercadorias'):
            kpis['valor_total_mercadorias'] = float(kpis['valor_total_mercadorias'])
            
        # Retorna o dicionário de kpis, ou um dicionário vazio se a tabela estiver vazia.
        return kpis or {}
    except Exception as e:
        logger.error(f"Erro ao buscar KPIs do dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar KPIs.")

@router.get("/operacoes_por_status")
@cached(cache)
def get_operacoes_por_status(cur = Depends(get_db_cursor)):
    logger.info("Buscando operações por status do banco (CACHE MISS)...")
    # A query já renomeia as colunas para "name" e "value", simplificando o trabalho do frontend.
    sql = "SELECT status as name, COUNT(*) as value FROM operacoes_logisticas GROUP BY status ORDER BY value DESC;"
    try:
        cur.execute(sql)
        # fetchall() busca todas as linhas do resultado e já retorna uma lista de dicionários.
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
        # Itera sobre os resultados para converter o tipo 'Decimal' para 'float'.
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
        # Itera sobre os resultados para formatar a data (que vem como objeto `datetime.date`) para o formato 'dd/mm'.
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
        # Converte o tipo 'Decimal' para 'float'.
        for row in data:
            if row.get('value'): row['value'] = float(row['value'])
        return data
    except Exception as e:
        logger.error(f"Erro ao buscar top clientes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar top clientes.")