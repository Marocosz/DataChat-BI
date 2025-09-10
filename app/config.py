from pathlib import Path

# --- Caminhos Base
# Define o diretório raiz do projeto (a pasta que contém a pasta 'app')
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configurações de Pastas e Arquivos de Dados
DATA_DIR = BASE_DIR / "data"
JSON_DATA_PATH = DATA_DIR / "dicionario_de_dados.json"
INVERTED_INDEX_PATH = DATA_DIR / "inverted_index.json"
DATABASE_NAME = "catalogo.db"
DATABASE_PATH = DATA_DIR / DATABASE_NAME