import json
import os
import sys

# --- Configuração de Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import JSON_DATA_PATH
from app.models import get_session, EsquemasCatalogados, TabelasCatalogadas, ColunasCatalogadas

def sincronizar_catalogo():
    """
    Função principal que orquestra todo o processo de sincronização.
    Ela lê o arquivo JSON (extração bruta do banco) e usa essa informação
    para popular ou atualizar o nosso banco de dados do catálogo (o SQLite).
    """
    
    print("--- INICIANDO SINCRONIZAÇÃO DO CATÁLOGO ---")

    # Inicia uma sessão com o banco de dados.
    session = get_session()
    
    # Começa a ler o json
    print(f"Lendo o arquivo de estrutura: '{JSON_DATA_PATH}'")
    try:
        # Abre o arquivo JSON em modo de leitura ('r') com codificação 'utf-8' 
        with open(JSON_DATA_PATH, 'r', encoding='utf-8') as f:
            # A função json.load() lê o arquivo e converte o texto JSON
            # em uma estrutura de dados Python (dicionários e listas).
            estrutura_bruta = json.load(f)
    except FileNotFoundError:
        # Se o arquivo JSON não existir interrompe a execução.
        print(f"ERRO: Arquivo '{JSON_DATA_PATH}' não encontrado. Execute o script 01 primeiro.")
        return

    # Itera sobre a estrutura de dados lida do JSON e popular nosso banco.
    # .items() nos dá tanto a chave (nome_schema) quanto o valor (tabelas_brutas) de cada item no dicionário.
    for nome_schema, tabelas_brutas in estrutura_bruta.items():
        print(f"\n[SCHEMA] Processando: '{nome_schema}'")
        
        # LÓGICA "UPSERT" (UPDATE + INSERT): Verificar se o registro já existe antes de criar.

        # Consulta nosso banco: "Existe algum registro na tabela 'Schema' onde o nome seja igual a 'nome_schema'?"
        schema_db = session.query(EsquemasCatalogados).filter_by(nome=nome_schema).first()
        
        # Se a consulta não retornou nada (ou seja, o schema é novo)...
        if not schema_db:
            # 1. Cria um novo objeto Schema em memória.
            schema_db = EsquemasCatalogados(nome=nome_schema)
            # 2. Adiciona o novo objeto à sessão, marcando-o como "para ser inserido".
            session.add(schema_db)
            # 3. session.flush(): Envia as instruções de inserção pendentes para o banco.
            #    Isso é importante para que o banco de dados gere o ID do novo schema,
            #    pois precisaremos desse ID para associar as tabelas a ele.
            session.flush()
            print(f" -> [NOVO] Schema '{nome_schema}' criado no catálogo.")
        
        for nome_tabela, dados_tabela in tabelas_brutas.items():
            print(f"  [TABELA] Verificando: '{nome_tabela}'")
            
            # Consulta nosso banco: "Existe alguma 'Tabela' com este nome_fisico E que pertença a este schema_id?"
            # A verificação dupla (nome e schema_id) evita conflitos se existirem tabelas com
            # o mesmo nome em schemas diferentes.
            tabela_db = session.query(TabelasCatalogadas).filter_by(nome_fisico=nome_tabela, schema_id=schema_db.id).first()
            
            # Se a tabela não existe no nosso catálogo...
            if not tabela_db:
                # Cria um novo objeto Tabela, já associando-o ao objeto schema_db que encontramos/criamos.
                tabela_db = TabelasCatalogadas(
                    esquema=schema_db,
                    nome_fisico=nome_tabela,
                    tipo_objeto=dados_tabela['tipo_objeto']
                )
                session.add(tabela_db)
                session.flush() # Força a geração do ID da nova tabela, para usarmos nas colunas.
                print(f"   -> [NOVO] Tabela '{nome_tabela}' criada no catálogo.")

            for coluna_bruta in dados_tabela['colunas']:
                # Consulta nosso banco: "Existe alguma 'Coluna' com este nome_fisico E que pertença a esta tabela_id?"
                coluna_db = session.query(ColunasCatalogadas).filter_by(nome_fisico=coluna_bruta['nome'], tabela_id=tabela_db.id).first()
                
                # Se a coluna não existe no nosso catálogo...
                if not coluna_db:
                    # Cria um novo objeto Coluna e o associa ao objeto tabela_db.
                    coluna_db = ColunasCatalogadas(
                        tabela=tabela_db,
                        nome_fisico=coluna_bruta['nome'],
                        tipo_dado=coluna_bruta['tipo'],
                        nulo=coluna_bruta['nulo'],
                        pk=coluna_bruta['pk']
                    )
                    session.add(coluna_db)
                    # Não usamos 'flush' aqui pois não precisamos do ID da coluna para nada em seguida neste loop.

    # Efetivar todas as alterações.
    print("\nSalvando todas as alterações no banco de dados do catálogo...")
    # session.commit(): "Finaliza a transação". Pega todas as operações pendentes (adds, updates, deletes)
    # que foram registradas na sessão e as envia para o banco de dados de uma só vez.
    # É o comando que torna as mudanças permanentes.
    session.commit()
    
    # Libera a conexão com o banco de dados.
    session.close()
    print("--- SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO ---")


if __name__ == "__main__":
    sincronizar_catalogo()