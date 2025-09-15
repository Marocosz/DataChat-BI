# backend/scripts/populate_db.py

import sqlite3
import os

# --- Configurações ---
DB_PATH = "backend/data"
DB_FILE = os.path.join(DB_PATH, "catalogo.db")

# ==============================================================================
# DICIONÁRIO DE TEMAS COM DADOS DE NEGÓCIO REALISTAS E EM PORTUGUÊS
# ==============================================================================
DATA_CATALOG_THEMES = {
    "Vendas": {
        "schema_prefix": "DW",
        "table_themes": [
            {
                "name": "Clientes", "type": "DIM",
                "description": "Tabela dimensão que armazena o cadastro mestre de todos os clientes da empresa, sejam eles pessoas físicas ou jurídicas. É a fonte única da verdade para informações de clientes.",
                "columns": [
                    ('ID_CLIENTE', 'INTEGER', 'ID do Cliente', 'Chave primária artificial (surrogate key) que identifica unicamente cada cliente no Data Warehouse.', True),
                    ('CD_CLIENTE_LEGADO', 'VARCHAR(50)', 'Código Legado do Cliente', 'Identificador do cliente no sistema de origem (ERP, CRM), usado para referência cruzada.', False),
                    ('NM_CLIENTE', 'VARCHAR(200)', 'Nome do Cliente', 'Nome completo para pessoa física ou razão social para pessoa jurídica.', False),
                    ('TIPO_PESSOA', 'CHAR(1)', 'Tipo de Pessoa (F/J)', 'Flag que identifica o cliente como Pessoa Física (F) ou Jurídica (J).', False),
                    ('DT_NASCIMENTO', 'DATE', 'Data de Nascimento', 'Data de nascimento para clientes PF, usada para análises demográficas e de idade.', False),
                    ('EMAIL_CONTATO', 'VARCHAR(100)', 'E-mail de Contato', 'Endereço de e-mail principal para comunicação e envio de faturas ou marketing.', False),
                    ('DT_CADASTRO', 'TIMESTAMP', 'Data de Cadastro', 'Data e hora exatas em que o registro do cliente foi criado no sistema.', False)
                ]
            },
            {
                "name": "Produtos", "type": "DIM",
                "description": "Dimensão de produtos, contendo o catálogo de todos os itens disponíveis para venda, seus atributos e classificações mercadológicas.",
                "columns": [
                    ('ID_PRODUTO', 'INTEGER', 'ID do Produto', 'Chave primária artificial (surrogate key) que identifica unicamente cada produto no Data Warehouse.', True),
                    ('CD_SKU', 'VARCHAR(50)', 'Código SKU do Produto', 'SKU (Stock Keeping Unit) único usado pelo sistema de inventário para rastrear o item.', False),
                    ('NM_PRODUTO', 'VARCHAR(250)', 'Nome do Produto', 'Nome comercial completo do produto, como exibido para o cliente.', False),
                    ('DS_CATEGORIA', 'VARCHAR(100)', 'Descrição da Categoria', 'Agrupamento principal do produto (ex: Eletrônicos, Vestuário, Alimentos).', False),
                    ('DS_MARCA', 'VARCHAR(100)', 'Descrição da Marca', 'Fabricante ou marca do produto, importante para filtros de afinidade.', False),
                    ('VL_PRECO_UNITARIO', 'DECIMAL(18,2)', 'Valor do Preço Unitário', 'Preço de prateleira padrão para uma unidade do produto, antes de descontos.', False)
                ]
            },
            {
                "name": "Lojas", "type": "DIM",
                "description": "Dimensão das lojas físicas e filiais da empresa, contendo informações de localização geográfica e responsabilidade gerencial.",
                "columns": [
                    ('ID_LOJA', 'INTEGER', 'ID da Loja', 'Chave primária que identifica unicamente cada loja ou centro de distribuição.', True),
                    ('NM_LOJA', 'VARCHAR(150)', 'Nome da Loja', 'Nome fantasia da filial ou loja para identificação em relatórios.', False),
                    ('DS_CIDADE', 'VARCHAR(100)', 'Cidade da Loja', 'Cidade onde a loja está fisicamente localizada.', False),
                    ('DS_ESTADO', 'CHAR(2)', 'Estado da Loja', 'Sigla da Unidade Federativa (UF) da loja.', False),
                    ('NM_GERENTE', 'VARCHAR(200)', 'Nome do Gerente Regional', 'Nome do gestor diretamente responsável pela filial.', False)
                ]
            },
            {
                "name": "Calendario", "type": "DIM",
                "description": "Tabela de dimensão de tempo, essencial para análises temporais. Contém atributos de data para facilitar a agregação por mês, trimestre, ano, etc.",
                "columns": [
                    ('ID_DATA', 'INTEGER', 'ID da Data (SK)', 'Chave primária no formato YYYYMMDD para ligação eficiente com tabelas fato.', True),
                    ('DATA_COMPLETA', 'DATE', 'Data Completa', 'Data no formato completo e legível (YYYY-MM-DD).', False),
                    ('NR_ANO', 'INTEGER', 'Número do Ano', 'Ano extraído da data, como 2025.', False),
                    ('NR_MES', 'INTEGER', 'Número do Mês', 'Mês numérico da data (1 a 12).', False),
                    ('NM_MES', 'VARCHAR(20)', 'Nome do Mês', 'Nome do mês por extenso (ex: Janeiro, Fevereiro).', False),
                    ('NR_TRIMESTRE', 'INTEGER', 'Número do Trimestre', 'Trimestre do ano ao qual a data pertence (1 a 4).', False),
                    ('NM_DIA_SEMANA', 'VARCHAR(20)', 'Nome do Dia da Semana', 'Dia da semana por extenso (ex: Segunda-feira).', False)
                ]
            },
            {
                "name": "Vendas", "type": "FAT",
                "description": "Tabela fato principal que registra as transações de venda na menor granularidade (item por pedido). É a base para a maioria das análises de performance de negócio.",
                "columns": [
                    ('ID_CLIENTE', 'INTEGER', 'ID do Cliente (FK)', 'Chave estrangeira (Foreign Key) que referencia a dimensão de clientes.', False),
                    ('ID_PRODUTO', 'INTEGER', 'ID do Produto (FK)', 'Chave estrangeira (Foreign Key) que referencia a dimensão de produtos.', False),
                    ('ID_LOJA', 'INTEGER', 'ID da Loja (FK)', 'Chave estrangeira (Foreign Key) que referencia a dimensão de lojas.', False),
                    ('ID_DATA_VENDA', 'INTEGER', 'ID da Data da Venda (FK)', 'Chave estrangeira para a dimensão calendário, ligando a venda a uma data específica.', False),
                    ('ID_PEDIDO', 'INTEGER', 'ID do Pedido de Venda', 'Identificador do pedido de venda ao qual o item pertence.', False),
                    ('QTD_VENDIDA', 'INTEGER', 'Quantidade Vendida', 'Número de unidades do produto vendidas nesta transação específica.', False),
                    ('VL_TOTAL_ITEM', 'DECIMAL(18,2)', 'Valor Total do Item', 'Receita gerada pelo item na venda (Quantidade * Preço Praticado).', False)
                ]
            }
        ]
    },
    "Recursos Humanos": {
        "schema_prefix": "DM",
        "table_themes": [
            {
                "name": "Colaboradores", "type": "DIM",
                "description": "Dimensão mestre de colaboradores, contendo todos os dados pessoais e profissionais dos funcionários da empresa.",
                "columns": [
                    ('ID_COLABORADOR', 'INTEGER', 'ID do Colaborador', 'Chave primária que identifica unicamente cada colaborador no sistema de RH.', True),
                    ('MATRICULA', 'VARCHAR(20)', 'Matrícula do Colaborador', 'Número de matrícula funcional, usado para identificação em sistemas internos.', False),
                    ('NM_COMPLETO', 'VARCHAR(250)', 'Nome Completo do Colaborador', 'Nome civil completo do colaborador.', False),
                    ('DS_CARGO', 'VARCHAR(100)', 'Descrição do Cargo', 'Cargo oficial ocupado pelo colaborador (ex: Analista Financeiro, Gerente de Vendas).', False),
                    ('DS_DEPARTAMENTO', 'VARCHAR(100)', 'Descrição do Departamento', 'Departamento de lotação do colaborador (ex: Contabilidade, TI, Marketing).', False),
                    ('DT_ADMISSAO', 'DATE', 'Data de Admissão', 'Data de início do vínculo empregatício do colaborador com a empresa.', False)
                ]
            },
        ]
    },
    "Finanças": {
        "schema_prefix": "DW",
        "table_themes": [
            {
                "name": "PlanoContas", "type": "DIM",
                "description": "Dimensão do plano de contas contábil, que é a estrutura hierárquica de todas as contas usadas para registrar transações financeiras.",
                "columns": [
                    ('ID_CONTA', 'INTEGER', 'ID da Conta Contábil', 'Chave primária da conta.', True),
                    ('CD_CONTA_CONTABIL', 'VARCHAR(30)', 'Código da Conta Contábil', 'Código estruturado e hierárquico da conta (ex: 1.01.02.001).', False),
                    ('DS_CONTA', 'VARCHAR(200)', 'Descrição da Conta', 'Nome descritivo da conta contábil (ex: Caixa, Fornecedores, Receita de Vendas).', False),
                    ('TIPO_CONTA', 'CHAR(1)', 'Tipo de Conta (A/P/R/D)', 'Define a natureza da conta: Ativo, Passivo, Receita ou Despesa.', False)
                ]
            },
            {
                "name": "LancamentosContabeis", "type": "FAT",
                "description": "Tabela fato com todos os lançamentos contábeis (débito e crédito) em sua menor granularidade. É a fonte primária para balancetes e DRE.",
                "columns": [
                    ('ID_LANCAMENTO', 'BIGINT', 'ID do Lançamento', 'Identificador único de cada transação contábil.', True),
                    ('ID_DATA_LANCAMENTO', 'INTEGER', 'ID da Data do Lançamento (FK)', 'Chave para a dimensão calendário, indicando quando a transação ocorreu.', False),
                    ('ID_CONTA_CONTABIL', 'INTEGER', 'ID da Conta Contábil (FK)', 'Chave para a dimensão de plano de contas.', False),
                    ('VL_DEBITO', 'DECIMAL(18,2)', 'Valor do Débito', 'Valor lançado a débito na conta. Se for um lançamento a crédito, este campo é zero.', False),
                    ('VL_CREDITO', 'DECIMAL(18,2)', 'Valor do Crédito', 'Valor lançado a crédito na conta. Se for um lançamento a débito, este campo é zero.', False),
                    ('DS_HISTORICO', 'VARCHAR(500)', 'Descrição do Histórico do Lançamento', 'Descrição textual detalhada que explica a natureza e o motivo do lançamento contábil.', False)
                ]
            }
        ]
    }
}

def recreate_tables(cursor):
    """Apaga as tabelas antigas e as recria com a estrutura correta."""
    print("Destruindo tabelas antigas (se existirem)...")
    cursor.execute("DROP TABLE IF EXISTS colunas_catalogadas;")
    cursor.execute("DROP TABLE IF EXISTS tabelas_catalogadas;")
    cursor.execute("DROP TABLE IF EXISTS esquemas_catalogados;")

    print("Criando novas tabelas...")
    cursor.execute("""
    CREATE TABLE esquemas_catalogados (id INTEGER PRIMARY KEY AUTOINCREMENT, nome VARCHAR(200) NOT NULL UNIQUE);
    """)
    cursor.execute("""
    CREATE TABLE tabelas_catalogadas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_fisico VARCHAR(200) NOT NULL, tipo_objeto VARCHAR(50) NOT NULL, nome_negocio VARCHAR(200), descricao TEXT, schema_id INTEGER NOT NULL, FOREIGN KEY (schema_id) REFERENCES esquemas_catalogados (id));
    """)
    cursor.execute("""
    CREATE TABLE colunas_catalogadas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_fisico VARCHAR(200) NOT NULL, tipo_dado VARCHAR(100), nulo BOOLEAN, pk BOOLEAN, nome_negocio VARCHAR(200), descricao TEXT, tabela_id INTEGER NOT NULL, FOREIGN KEY (tabela_id) REFERENCES tabelas_catalogadas (id));
    """)
    print("Tabelas recriadas com sucesso!")

def populate_data(cursor):
    """Popula as tabelas usando a estrutura temática DATA_CATALOG_THEMES."""
    print("Iniciando a população de dados com coerência contextual...")

    total_tables = 0
    total_columns = 0

    for area, theme in DATA_CATALOG_THEMES.items():
        schema_name = f"{theme['schema_prefix']}_{area.upper()}"
        cursor.execute("INSERT INTO esquemas_catalogados (nome) VALUES (?)", (schema_name,))
        schema_id = cursor.lastrowid
        print(f"\nCriando esquema: '{schema_name}'")

        for table_theme in theme['table_themes']:
            table_name_part = table_theme['name'].upper()
            table_type_part = table_theme['type']
            
            nome_fisico = f"TBL_{table_type_part}_{table_name_part}"
            nome_negocio = f"{'Dimensão de' if table_type_part == 'DIM' else 'Fato'} {table_theme['name']}"
            descricao = table_theme['description']
            tipo_objeto = 'TABLE'

            cursor.execute("""
                INSERT INTO tabelas_catalogadas (nome_fisico, tipo_objeto, nome_negocio, descricao, schema_id)
                VALUES (?, ?, ?, ?, ?)
            """, (nome_fisico, tipo_objeto, nome_negocio, descricao, schema_id))
            table_id = cursor.lastrowid
            total_tables += 1
            print(f"  -> Criando tabela: '{nome_fisico}' ({nome_negocio})")

            for col in table_theme['columns']:
                col_nome_fisico, col_tipo_dado, col_nome_negocio, col_descricao, is_pk = col
                nulo = not is_pk

                cursor.execute("""
                    INSERT INTO colunas_catalogadas (nome_fisico, tipo_dado, nulo, pk, nome_negocio, descricao, tabela_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (col_nome_fisico, col_tipo_dado, nulo, is_pk, col_nome_negocio, col_descricao, table_id))
                total_columns += 1

    print(f"\n--------------------------------------------------")
    print(f"Resumo da Geração:")
    print(f"- {len(DATA_CATALOG_THEMES)} esquemas criados.")
    print(f"- {total_tables} tabelas criadas.")
    print(f"- {total_columns} colunas criadas.")
    print(f"--------------------------------------------------")

def main():
    """Função principal que orquestra a criação e população do banco de dados."""
    try:
        os.makedirs(DB_PATH, exist_ok=True)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        recreate_tables(cursor)
        populate_data(cursor)
        
        conn.commit()
        print(f"\n🎉 Operação concluída! O banco de dados '{DB_FILE}' foi populado com metadados de alta qualidade.")
        
    except sqlite3.Error as e:
        print(f"Ocorreu um erro no banco de dados: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    main()