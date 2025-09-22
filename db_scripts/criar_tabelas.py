# =============================================================================
# SCRIPT PARA CRIAÇÃO E SETUP DA ESTRUTURA DO BANCO DE DADOS
#
# Este script é responsável por construir todo o alicerce do banco de dados
# PostgreSQL. Ele cria as tabelas 'clientes' e 'operacoes_logisticas', 
# os tipos de dados customizados (ENUMs) e os índices de performance.
#
# NOTA: O script é IDEMPOTENTE e NÃO DESTRUTIVO. Graças ao uso de 
# 'IF NOT EXISTS', ele pode ser executado múltiplas vezes sem apagar
# dados ou causar erros. Ele apenas criará as estruturas que estiverem 
# faltando.
# =============================================================================

import os
import psycopg2
import psycopg2.errors
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente do script
load_dotenv()

# --- SCRIPT SQL COMPLETO PARA CRIAÇÃO DO BANCO DE DADOS ---
SQL_SETUP_SCRIPT = """
-- Etapa 1: Criação dos tipos ENUM (se não existirem)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_operacao_logistica') THEN
        CREATE TYPE tipo_operacao_logistica AS ENUM ('TRANSPORTE', 'ARMAZENAGEM');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_operacao') THEN
        CREATE TYPE status_operacao AS ENUM (
            'SOLICITADO',
            'AGUARDANDO_COLETA',
            'EM_TRANSITO',
            'ARMAZENADO',
            'EM_ROTA_DE_ENTREGA',
            'ENTREGUE',
            'CANCELADO'
        );
    END IF;
END$$;

-- Etapa 2: Criação da tabela de suporte 'clientes' (se não existir)
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome_razao_social VARCHAR(255) NOT NULL,
    cnpj_cpf VARCHAR(18) UNIQUE NOT NULL,
    email_contato VARCHAR(100),
    telefone_contato VARCHAR(20),
    data_cadastro TIMESTAMPTZ DEFAULT NOW()
);

-- Etapa 3: Criação da tabela principal 'operacoes_logisticas' (se não existir)
CREATE TABLE IF NOT EXISTS operacoes_logisticas (
    id BIGSERIAL PRIMARY KEY,
    codigo_operacao VARCHAR(20) UNIQUE NOT NULL,
    tipo tipo_operacao_logistica NOT NULL,
    status status_operacao NOT NULL DEFAULT 'SOLICITADO',
    
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    
    data_emissao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_previsao_entrega DATE,
    data_entrega_realizada TIMESTAMPTZ,
    
    uf_coleta VARCHAR(2) NOT NULL,
    cidade_coleta VARCHAR(100) NOT NULL,
    uf_destino VARCHAR(2) NOT NULL,
    cidade_destino VARCHAR(100) NOT NULL,
    
    peso_kg NUMERIC(10, 3) NOT NULL,
    quantidade_volumes INT NOT NULL,
    valor_mercadoria NUMERIC(12, 2) NOT NULL,
    natureza_carga VARCHAR(100),
    
    valor_frete NUMERIC(10, 2),
    valor_seguro NUMERIC(10, 2),
    
    codigo_rastreio VARCHAR(50),
    observacoes TEXT,
    
    CONSTRAINT check_peso_positivo CHECK (peso_kg > 0),
    CONSTRAINT check_quantidade_positiva CHECK (quantidade_volumes > 0),
    CONSTRAINT check_valor_mercadoria_positivo CHECK (valor_mercadoria >= 0)
);

-- Etapa 4: Criação dos índices para performance (se não existirem)
CREATE INDEX IF NOT EXISTS idx_status ON operacoes_logisticas (status);
CREATE INDEX IF NOT EXISTS idx_cliente_id ON operacoes_logisticas (cliente_id);
CREATE INDEX IF NOT EXISTS idx_codigo_operacao ON operacoes_logisticas (codigo_operacao);
CREATE INDEX IF NOT EXISTS idx_cnpj_cpf_cliente ON clientes (cnpj_cpf);
"""

def setup_database():
    """
    Função principal para conectar ao PostgreSQL e executar o script de setup.
    """
    try:
        db_params = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "database": os.getenv("DB_DATABASE"),
            "user": os.getenv("DB_USERNAME"),
            "password": os.getenv("DB_PASSWORD"),
            "client_encoding": "utf8"
        }
        
        # Validação para garantir que todas as variáveis foram carregadas
        if not all(db_params.values()):
            print("❌ ERRO: Uma ou mais variáveis de ambiente do banco de dados não foram definidas.")
            return

        # Conectando ao banco de dados PostgreSQL
        print("🔌 Conectando ao banco de dados PostgreSQL...")
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                print("🚀 Executando o script de setup do banco de dados...")
                cur.execute(SQL_SETUP_SCRIPT)
                
                print("\n✅ Script executado com sucesso!")
                print("   - Tipos ENUM verificados/criados.")
                print("   - Tabela 'clientes' verificada/criada.")
                print("   - Tabela 'operacoes_logisticas' verificada/criada.")
                print("   - Índices de performance verificados/criados.")
                print("\n✨ Seu banco de dados está pronto para ser usado! ✨")

    except psycopg2.OperationalError as e:
        print(f"\n❌ ERRO DE CONEXÃO: Não foi possível conectar ao banco de dados.")
        print(f"   Detalhes: {e}")
        
    except psycopg2.Error as e:
        print(f"\n❌ Ocorreu um erro inesperado do PostgreSQL:")
        print(f"   Detalhes: {e}")

if __name__ == '__main__':
    setup_database()