
import sqlite3
import json
import argparse
import sys

def export_db_to_dict(db_path: str) -> dict:
    """
    Exporta todos os dados de todas as tabelas de um banco de dados SQLite
    para um dicionário Python.

    Args:
        db_path: O caminho para o arquivo do banco de dados .db.

    Returns:
        Um dicionário contendo os dados de todas as tabelas.
    """
    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        # Esta linha é a chave: transforma a saída de tuplas para objetos
        # que se comportam como dicionários, facilitando a conversão para JSON.
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()

        all_data = {}

        # 1. Obter a lista de todas as tabelas, ignorando as tabelas internas do SQLite
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()

        # 2. Iterar sobre cada tabela para extrair os dados
        for table in tables:
            table_name = table['name']
            
            print(f"  - Lendo dados da tabela '{table_name}'...")
            
            # Seleciona todos os dados da tabela
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Converte cada linha (que é um objeto sqlite3.Row) para um dicionário
            # e adiciona à lista de dados daquela tabela.
            all_data[table_name] = [dict(row) for row in rows]

    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}", file=sys.stderr)
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            
    return all_data

def save_data_to_json(data: dict, output_path: str):
    """
    Salva o dicionário de dados em um arquivo JSON.

    Args:
        data: O dicionário com os dados do banco.
        output_path: O caminho para o arquivo JSON de saída.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Dados exportados com sucesso para: {output_path}")
    except IOError as e:
        print(f"Erro ao salvar o arquivo JSON: {e}", file=sys.stderr)

def main():
    """
    Função principal para executar o script via linha de comando.
    """
    parser = argparse.ArgumentParser(
        description="Exporta TODOS OS DADOS de um banco de dados SQLite (.db) para um arquivo JSON."
    )
    parser.add_argument("db_file", help="Caminho para o arquivo de banco de dados .db de entrada.")
    parser.add_argument("json_file", help="Caminho para o arquivo .json de saída.")
    
    args = parser.parse_args()

    print(f"🔎 Iniciando exportação de dados de '{args.db_file}'...")
    db_data = export_db_to_dict(args.db_file)
    
    if db_data:
        save_data_to_json(db_data, args.json_file)

if __name__ == "__main__":
    main()