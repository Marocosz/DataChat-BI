# =============================================================================
# SCRIPT PARA POPULAR O BANCO DE DADOS COM DADOS DE TESTE
# 
# AVISO: Este script apaga TODOS os dados das tabelas 'clientes' e 
# 'operacoes_logisticas' antes de inserir novos dados. NÃO RODE EM PRODUÇÃO.
#
# O script usa a biblioteca Faker para gerar dados realistas e os insere em
# massa para melhor performance. 
# =============================================================================
import os
from pathlib import Path
import random
import psycopg2
import io
from faker import Faker
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime, timedelta

# Define o caminho para a raiz do projeto (um nível acima do db_scripts)
BASE_DIR = Path(__file__).resolve().parent.parent
# Carrega as variáveis do arquivo .env para o ambiente do script
load_dotenv(BASE_DIR / "backend" / ".env")
# --- CONFIGURAÇÕES ---
NUMERO_DE_CLIENTES = 120
NUMERO_DE_OPERACOES = 250000 

# Inicializa o Faker para gerar dados em Português do Brasil
fake = Faker('pt_BR')

# Lista de locais para tornar os dados mais realistas (Cidade, UF)
LOCAIS_BRASIL = [
    ('São Paulo', 'SP'), ('Rio de Janeiro', 'RJ'), ('Belo Horizonte', 'MG'),
    ('Curitiba', 'PR'), ('Porto Alegre', 'RS'), ('Salvador', 'BA'),
    ('Recife', 'PE'), ('Fortaleza', 'CE'), ('Brasília', 'DF'),
    ('Manaus', 'AM'), ('Goiânia', 'GO'), ('Belém', 'PA'),
    ('Campinas', 'SP'), ('Santos', 'SP'), ('Uberlândia', 'MG'),
    ('Joinville', 'SC'), ('Caxias do Sul', 'RS'), ('Vitória', 'ES')
]

# Listas de opções para os campos de operação
TIPOS_OPERACAO = ['TRANSPORTE', 'ARMAZENAGEM']
STATUS_OPERACAO = ['SOLICITADO', 'AGUARDANDO_COLETA', 'EM_TRANSITO', 'ARMAZENADO', 'ENTREGUE', 'CANCELADO']
NATUREZA_CARGA = ['Eletrônicos', 'Peças Automotivas', 'Alimentos Não Perecíveis', 'Têxteis', 'Cosméticos', 'Móveis', 'Farmacêuticos']
OBSERVACOES_TEMPLATES = [
    "Entregar em horário comercial.", "Cuidado: Carga frágil.",
    "Deixar na portaria com o Sr. {nome}.", "Agendar entrega por telefone.",
    "Urgente. Prioridade máxima.", "Verificar documentação no ato da entrega.",
    None, None, None,
]


def popular_banco():
    """
    Função principal para conectar ao banco e popular as tabelas.
    """
    try:
        db_params = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "database": os.getenv("DB_NAME"),       
            "user": os.getenv("DB_USER"),      
            "password": os.getenv("DB_PASS"),       
            "client_encoding": "utf8",
            "sslmode": "require"
        }
        
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                print("Conexão bem-sucedida. Iniciando a população do banco de dados...")

                # --- 1. Limpar tabelas ---
                print("Limpando dados existentes...")
                cur.execute("TRUNCATE TABLE clientes RESTART IDENTITY CASCADE;")

                # --- 2. Gerar e Inserir Clientes (COM LÓGICA DE PF/PJ) ---
                print(f"Gerando {NUMERO_DE_CLIENTES} clientes (PF e PJ)...")
                clientes_para_inserir = []
                # <--- ALTERADO: Lógica para gerar PF e PJ ---
                for _ in range(NUMERO_DE_CLIENTES):
                    # Decide aleatoriamente (80% de chance de ser PJ)
                    if random.choices(['PJ', 'PF'], weights=[80, 20], k=1)[0] == 'PJ':
                        nome = fake.company()
                        documento = fake.cnpj()
                        email = f"contato@{nome.lower().replace(' ', '').replace(',', '')[:15]}.com"
                    else:
                        nome = fake.name()
                        documento = fake.cpf()
                        email = f"{nome.lower().replace(' ', '.')}@{fake.free_email_domain()}"
                    
                    telefone = fake.phone_number()
                    clientes_para_inserir.append((nome, documento, email, telefone))
                
                print("Inserindo clientes no banco de dados...")
                sql_insert_clientes = "INSERT INTO clientes (nome_razao_social, cnpj_cpf, email_contato, telefone_contato) VALUES (%s, %s, %s, %s) RETURNING id;"
                
                id_clientes = []
                for record in clientes_para_inserir:
                    cur.execute(sql_insert_clientes, record)
                    id_clientes.append(cur.fetchone()[0])
                
                print(f"{len(id_clientes)} clientes inseridos com sucesso.")

                # --- 3. Gerar Operações Logísticas (em memória) ---
                print(f"Gerando {NUMERO_DE_OPERACOES} operações logísticas...")
                operacoes_para_inserir = []
                for i in range(NUMERO_DE_OPERACOES):
                    cliente_id = random.choice(id_clientes)
                    origem = random.choice(LOCAIS_BRASIL)
                    destino = random.choice([loc for loc in LOCAIS_BRASIL if loc != origem])
                    
                    status = random.choices(STATUS_OPERACAO, weights=[10, 10, 30, 10, 35, 5], k=1)[0]
                    data_emissao = fake.date_time_between(start_date='-2y', end_date='now', tzinfo=None)
                    data_previsao_entrega = data_emissao + timedelta(days=random.randint(2, 15))
                    data_entrega_realizada = None
                    if status == 'ENTREGUE':
                        data_entrega_realizada = data_previsao_entrega + timedelta(days=random.randint(-2, 1))

                    valor_mercadoria = Decimal(str(round(random.uniform(500.00, 50000.00), 2)))
                    valor_frete = valor_mercadoria * Decimal(str(random.uniform(0.05, 0.15)))
                    valor_seguro = valor_mercadoria * Decimal(str(random.uniform(0.003, 0.015)))
                    
                    observacao_template = random.choice(OBSERVACOES_TEMPLATES)
                    observacao = observacao_template.format(nome=fake.first_name()) if observacao_template and '{nome}' in observacao_template else observacao_template
                    
                    operacao = (
                        f"OP-{data_emissao.year}-{i+1:06d}", random.choice(TIPOS_OPERACAO), status, cliente_id, data_emissao,
                        data_previsao_entrega.date(), data_entrega_realizada, origem[1], origem[0], destino[1], destino[0],
                        Decimal(str(round(random.uniform(5.5, 2000.0), 3))), random.randint(1, 50),
                        valor_mercadoria, random.choice(NATUREZA_CARGA),
                        valor_frete.quantize(Decimal('0.01')), 
                        valor_seguro.quantize(Decimal('0.01')), 
                        fake.bothify(text='??#########??').upper(),
                        observacao
                    )
                    operacoes_para_inserir.append(operacao)
                
                # --- 4. Inserir Operações Logísticas (em massa com COPY) ---
                print("Inserindo operações no banco de dados com COPY...")
                buffer = io.StringIO()
                for operacao in operacoes_para_inserir:
                    linha = '\t'.join(str(v).replace('\t', ' ') if v is not None else '\\N' for v in operacao)
                    buffer.write(linha + '\n')
                
                buffer.seek(0)
                
                colunas = (
                    'codigo_operacao', 'tipo', 'status', 'cliente_id', 'data_emissao', 'data_previsao_entrega', 
                    'data_entrega_realizada', 'uf_coleta', 'cidade_coleta', 'uf_destino', 'cidade_destino', 
                    'peso_kg', 'quantidade_volumes', 'valor_mercadoria', 'natureza_carga', 'valor_frete', 
                    'valor_seguro', 'codigo_rastreio', 'observacoes'
                )
                cur.copy_from(buffer, 'operacoes_logisticas', columns=colunas, sep='\t')
                
                print(f"{cur.rowcount} operações inseridas com sucesso.")
                print("\n✅ População do banco de dados concluída!")

    except psycopg2.OperationalError as e:
        print(f"\n❌ ERRO DE CONEXÃO: Não foi possível conectar ao banco de dados.")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado: {e}")


if __name__ == '__main__':
    popular_banco()