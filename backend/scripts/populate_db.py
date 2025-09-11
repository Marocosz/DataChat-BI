import sqlite3
import random
from faker import Faker

# --- Configurações ---
DB_FILE = "data/catalogo.db"

# Inicializa o Faker para detalhes menores
fake = Faker('pt_BR')

# ==============================================================================
# O NOVO CÉREBRO: DICIONÁRIO DE TEMAS PARA GERAÇÃO CONTEXTUAL
# ==============================================================================
DATA_CATALOG_THEMES = {
    "Vendas": {
        "schema_prefix": "DW",
        "table_themes": [
            {
                "name": "Clientes", "type": "DIM",
                "description": "Tabela dimensão que armazena o cadastro de todos os clientes da empresa, com dados demográficos e de contato. É a fonte única da verdade para informações de clientes.",
                "columns": [
                    ('ID_CLIENTE', 'INTEGER', 'ID do Cliente', 'Chave primária artificial (surrogate key) para a dimensão de clientes.', True),
                    ('CD_CLIENTE_LEGADO', 'VARCHAR(50)', 'Código Legado do Cliente', 'Código do cliente no sistema de origem (ERP).', False),
                    ('NM_CLIENTE', 'VARCHAR(200)', 'Nome do Cliente', 'Nome completo ou razão social do cliente.', False),
                    ('TIPO_PESSOA', 'CHAR(1)', 'Tipo de Pessoa (F/J)', 'Indica se o cliente é Pessoa Física (F) ou Jurídica (J).', False),
                    ('DT_NASCIMENTO', 'DATE', 'Data de Nascimento', 'Data de nascimento para clientes do tipo pessoa física.', False),
                    ('EMAIL_CONTATO', 'VARCHAR(100)', 'E-mail de Contato', 'Endereço de e-mail principal para contato com o cliente.', False),
                    ('DT_CADASTRO', 'TIMESTAMP', 'Data de Cadastro', 'Data e hora em que o cliente foi inserido no sistema.', False)
                ]
            },
            {
                "name": "Produtos", "type": "DIM",
                "description": "Dimensão de produtos, contendo a lista de todos os itens disponíveis para venda, suas categorias, subcategorias e atributos.",
                "columns": [
                    ('ID_PRODUTO', 'INTEGER', 'ID do Produto', 'Chave primária artificial (surrogate key) para a dimensão de produtos.', True),
                    ('CD_SKU', 'VARCHAR(50)', 'Código SKU do Produto', 'SKU (Stock Keeping Unit) único para identificação do produto.', False),
                    ('NM_PRODUTO', 'VARCHAR(250)', 'Nome do Produto', 'Nome comercial do produto.', False),
                    ('DS_CATEGORIA', 'VARCHAR(100)', 'Descrição da Categoria', 'Categoria principal a qual o produto pertence.', False),
                    ('DS_MARCA', 'VARCHAR(100)', 'Descrição da Marca', 'Marca do produto.', False),
                    ('VL_PRECO_UNITARIO', 'DECIMAL(18,2)', 'Valor do Preço Unitário', 'Preço de venda padrão para uma unidade do produto.', False)
                ]
            },
            {
                "name": "Vendas", "type": "FAT",
                "description": "Tabela fato principal que armazena cada item de venda individualmente, permitindo análises de performance, quantidade e valores transacionados. É granular no nível de item por pedido.",
                "columns": [
                    ('ID_CLIENTE', 'INTEGER', 'ID do Cliente (FK)', 'Chave estrangeira que referencia a tabela de dimensão de clientes.', False),
                    ('ID_PRODUTO', 'INTEGER', 'ID do Produto (FK)', 'Chave estrangeira que referencia a tabela de dimensão de produtos.', False),
                    ('ID_PEDIDO', 'INTEGER', 'ID do Pedido', 'Identificador do pedido de venda ao qual o item pertence.', False),
                    ('DT_VENDA', 'DATE', 'Data da Venda', 'Data em que a transação de venda ocorreu.', False),
                    ('QTD_VENDIDA', 'INTEGER', 'Quantidade Vendida', 'Número de unidades do produto vendidas nesta transação.', False),
                    ('VL_UNITARIO_PRATICADO', 'DECIMAL(18,2)', 'Valor Unitário Praticado', 'Preço unitário do produto no momento da venda, pode incluir descontos.', False),
                    ('VL_TOTAL_ITEM', 'DECIMAL(18,2)', 'Valor Total do Item', 'Valor total para o item (Quantidade * Valor Unitário).', False)
                ]
            }
        ]
    },
    "Recursos Humanos": {
        "schema_prefix": "DM",
        "table_themes": [
            {
                "name": "Colaboradores", "type": "DIM",
                "description": "Armazena informações cadastrais e de carreira dos colaboradores ativos e inativos da organização.",
                "columns": [
                    ('ID_COLABORADOR', 'INTEGER', 'ID do Colaborador', 'Chave primária da tabela de colaboradores.', True),
                    ('MATRICULA', 'VARCHAR(20)', 'Matrícula do Colaborador', 'Número de matrícula funcional do colaborador.', False),
                    ('NM_COMPLETO', 'VARCHAR(250)', 'Nome Completo', 'Nome completo do colaborador.', False),
                    ('CPF', 'VARCHAR(11)', 'CPF', 'Cadastro de Pessoa Física do colaborador.', False),
                    ('DS_CARGO', 'VARCHAR(100)', 'Descrição do Cargo', 'Cargo atual ocupado pelo colaborador.', False),
                    ('DS_DEPARTAMENTO', 'VARCHAR(100)', 'Descrição do Departamento', 'Departamento de lotação do colaborador.', False),
                    ('DT_ADMISSAO', 'DATE', 'Data de Admissão', 'Data de início do contrato de trabalho.', False),
                    ('DT_DESLIGAMENTO', 'DATE', 'Data de Desligamento', 'Data de término do contrato de trabalho, se aplicável.', False)
                ]
            },
            {
                "name": "FolhaPagamento", "type": "FAT",
                "description": "Tabela fato mensal com os valores calculados da folha de pagamento para cada colaborador, incluindo proventos e descontos.",
                "columns": [
                    ('ID_COLABORADOR', 'INTEGER', 'ID do Colaborador (FK)', 'Chave de ligação com a dimensão de colaboradores.', False),
                    ('DT_COMPETENCIA', 'DATE', 'Data de Competência', 'Mês e ano a que se refere o pagamento (geralmente o último dia do mês).', False),
                    ('VL_SALARIO_BASE', 'DECIMAL(18,2)', 'Valor do Salário Base', 'Salário contratual do colaborador para a competência.', False),
                    ('VL_PROVENTOS', 'DECIMAL(18,2)', 'Valor Total de Proventos', 'Soma de todos os ganhos (salário, bônus, horas extras).', False),
                    ('VL_DESCONTOS', 'DECIMAL(18,2)', 'Valor Total de Descontos', 'Soma de todas as deduções (INSS, IRRF, vales).', False),
                    ('VL_LIQUIDO', 'DECIMAL(18,2)', 'Valor Líquido', 'Valor final a ser pago ao colaborador (Proventos - Descontos).', False)
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

    # Itera sobre cada área de negócio definida no nosso "cérebro"
    for area, theme in DATA_CATALOG_THEMES.items():
        # --- 1. Cria o Esquema ---
        schema_name = f"{theme['schema_prefix']}_{area.upper()}"
        cursor.execute("INSERT INTO esquemas_catalogados (nome) VALUES (?)", (schema_name,))
        schema_id = cursor.lastrowid
        print(f"\nCriando esquema: '{schema_name}'")

        # --- 2. Cria as Tabelas dentro do Esquema ---
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

            # --- 3. Cria as Colunas dentro da Tabela ---
            for col in table_theme['columns']:
                col_nome_fisico, col_tipo_dado, col_nome_negocio, col_descricao, is_pk = col
                nulo = not is_pk # Regra simples: PK não pode ser nula, outras podem

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
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        recreate_tables(cursor)
        populate_data(cursor)
        
        conn.commit()
        print("\n🎉 Operação concluída! O banco de dados foi populado com dados de alta qualidade contextual.")
        
    except sqlite3.Error as e:
        print(f"Ocorreu um erro no banco de dados: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    main()