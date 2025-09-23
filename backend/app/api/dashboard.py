# =============================================================================
# API ROUTER PARA O DASHBOARD
#
# Este módulo define os endpoints específicos para fornecer dados agregados
# para a página de dashboard do frontend.
#
# Usamos um APIRouter para agrupar estas rotas relacionadas, o que torna
# a aplicação principal mais modular e fácil de manter.
# =============================================================================

import logging
# Usamos o psycopg2 para executar queries SQL diretas e otimizadas para o dashboard.
import psycopg2
# APIRouter nos permite criar um conjunto de rotas que podem ser importadas na app principal.
# HTTPException é usado para retornar erros HTTP de forma padronizada.
from fastapi import APIRouter, HTTPException
# Importamos nossas configurações para obter as credenciais do banco de dados.
from app.core.config import settings

# --- Configuração Inicial ---
# Cria um logger e um router específicos para este módulo.
logger = logging.getLogger(__name__)
router = APIRouter()

def get_db_conn():
    """
    Função auxiliar para criar e retornar uma conexão com o banco de dados.
    Centraliza a lógica de conexão e o tratamento de erros iniciais.
    """
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASS,
            port=settings.DB_PORT
        )
        return conn
    except Exception as e:
        # Se a conexão falhar, loga o erro e levanta uma exceção HTTP 500.
        logger.error(f"Erro de conexão com o banco de dados: {e}")
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao banco de dados.")

# --- Definição dos Endpoints ---

# Define a rota GET para /api/dashboard/kpis
@router.get("/kpis")
def get_dashboard_kpis():
    """
    Retorna os principais indicadores de desempenho (KPIs) para os cards do dashboard.
    Executa uma única query otimizada para buscar todos os KPIs de uma vez.
    """
    # Query SQL que calcula os KPIs de forma agregada.
    sql = """
    SELECT
        COUNT(*) AS total_operacoes,
        SUM(CASE WHEN status = 'ENTREGUE' THEN 1 ELSE 0 END) AS operacoes_entregues,
        SUM(CASE WHEN status = 'EM_TRANSITO' THEN 1 ELSE 0 END) AS operacoes_em_transito,
        SUM(valor_mercadoria) AS valor_total_mercadorias
    FROM operacoes_logisticas;
    """
    conn = get_db_conn()
    try:
        # O 'with' garante que o cursor será fechado automaticamente.
        with conn.cursor() as cur:
            cur.execute(sql)
            # .fetchone() pega a primeira (e única) linha do resultado.
            kpis = cur.fetchone()
            if kpis:
                # Monta o dicionário de resposta com os resultados da query.
                return {
                    "total_operacoes": kpis[0],
                    "operacoes_entregues": kpis[1],
                    "operacoes_em_transito": kpis[2],
                    # Converte o tipo 'Decimal' do banco para 'float' para ser compatível com JSON.
                    "valor_total_mercadorias": float(kpis[3]) if kpis[3] else 0
                }
            return {} # Retorna um dicionário vazio se não houver dados.
    finally:
        # O bloco 'finally' garante que a conexão com o banco SEMPRE será fechada,
        # mesmo que ocorra um erro, evitando vazamento de recursos.
        conn.close()

# Define a rota GET para /api/dashboard/operacoes_por_status
@router.get("/operacoes_por_status")
def get_operacoes_por_status():
    """
    Retorna a contagem de operações agrupadas por status, formatada para
    ser usada diretamente pela biblioteca de gráficos Recharts no frontend.
    """
    sql = "SELECT status, COUNT(*) as count FROM operacoes_logisticas GROUP BY status ORDER BY count DESC;"
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            data = cur.fetchall()
            # Transforma a lista de tuplas (ex: [('ENTREGUE', 50), ('EM_TRANSITO', 20)])
            # em uma lista de dicionários no formato que o Recharts espera (ex: [{'name': 'ENTREGUE', 'value': 50}, ...]).
            return [{"name": str(row[0]), "value": row[1]} for row in data]
    finally:
        conn.close()
        

@router.get("/valor_frete_por_uf")
def get_valor_frete_por_uf():
    """
    Retorna o valor total de frete agrupado por UF de destino.
    Limita aos 10 estados com maior valor para um gráfico mais limpo.
    """
    sql = """
        SELECT uf_destino, SUM(valor_frete) as total_frete
        FROM operacoes_logisticas
        WHERE valor_frete IS NOT NULL
        GROUP BY uf_destino
        ORDER BY total_frete DESC
        LIMIT 10;
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            data = cur.fetchall()
            return [{"name": row[0], "value": float(row[1])} for row in data]
    finally:
        conn.close()

@router.get("/operacoes_por_dia")
def get_operacoes_por_dia():
    """
    Retorna a contagem de operações criadas por dia nos últimos 30 dias.
    Ideal para um gráfico de linha de tendência.
    """
    # CAST(data_emissao AS DATE) remove a parte de hora, agrupando por dia.
    sql = """
        SELECT CAST(data_emissao AS DATE) as dia, COUNT(*) as count
        FROM operacoes_logisticas
        WHERE data_emissao >= NOW() - INTERVAL '30 days'
        GROUP BY dia
        ORDER BY dia ASC;
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            data = cur.fetchall()
            # Formata a data para o padrão 'DD/MM' para exibição no gráfico
            return [{"name": row[0].strftime('%d/%m'), "value": row[1]} for row in data]
    finally:
        conn.close()
        

@router.get("/top_clientes_por_valor")
def get_top_clientes_por_valor():
    """
    Retorna os 5 maiores clientes com base no valor total de mercadorias movimentadas.
    Ideal para um gráfico de pizza.
    """
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
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            data = cur.fetchall()
            return [{"name": row[0], "value": float(row[1])} for row in data]
    finally:
        conn.close()