import sqlite3
import json
import argparse
import sys

def get_db_schema(db_path: str) -> dict:
    """
    Lê a estrutura de um banco de dados SQLite e a retorna como um dicionário.

    Args:
        db_path: O caminho para o arquivo do banco de dados .db.

    Returns:
        Um dicionário representando o esquema do banco de dados.
    """
    try:
        # Conecta ao banco de dados em modo somente leitura para segurança
        # A URI `?mode=ro` garante que não modificaremos o arquivo.
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        cursor = conn.cursor()

        schema = {}

        # 1. Obter a lista de todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()

        # 2. Para cada tabela, obter as informações das colunas
        for table in tables:
            table_name = table[0]
            schema[table_name] = []
            
            # O comando PRAGMA table_info é específico do SQLite para obter metadados da tabela
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            
            for column in columns:
                # O resultado de PRAGMA table_info é uma tupla com os seguintes índices:
                # 0: cid (ID da coluna)
                # 1: name (Nome da coluna)
                # 2: type (Tipo de dado, ex: TEXT, INTEGER)
                # 3: notnull (0 ou 1)
                # 4: dflt_value (Valor padrão)
                # 5: pk (1 se for parte da chave primária, 0 caso contrário)
                column_info = {
                    "name": column[1],
                    "type": column[2],
                    "not_null": bool(column[3]),
                    "default_value": column[4],
                    "is_primary_key": bool(column[5])
                }
                schema[table_name].append(column_info)

    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}", file=sys.stderr)
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            
    return schema

def save_schema_to_json(schema: dict, output_path: str):
    """
    Salva o dicionário do esquema em um arquivo JSON.

    Args:
        schema: O dicionário do esquema do banco de dados.
        output_path: O caminho para o arquivo JSON de saída.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # `indent=4` formata o JSON para ser legível por humanos
            json.dump(schema, f, indent=4, ensure_ascii=False)
        print(f"✅ Estrutura salva com sucesso em: {output_path}")
    except IOError as e:
        print(f"Erro ao salvar o arquivo JSON: {e}", file=sys.stderr)

def main():
    """
    Função principal para executar o script via linha de comando.
    """
    parser = argparse.ArgumentParser(
        description="Extrai a estrutura de um banco de dados SQLite (.db) para um arquivo JSON."
    )
    parser.add_argument("db_file", help="Caminho para o arquivo de banco de dados .db de entrada.")
    parser.add_argument("json_file", help="Caminho para o arquivo .json de saída.")
    
    args = parser.parse_args()

    print(f"🔎 Lendo a estrutura de '{args.db_file}'...")
    db_schema = get_db_schema(args.db_file)
    
    if db_schema:
        save_schema_to_json(db_schema, args.json_file)

if __name__ == "__main__":
    main()