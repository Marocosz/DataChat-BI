# Importa as ferramentas necessárias da biblioteca SQLAlchemy
# create_engine: Para conectar ao banco de dados.
# Column, Integer, String, Text, ForeignKey, Boolean: Para definir os tipos de dados das colunas.
# declarative_base: Uma função que cria uma classe base para nossos modelos.
# relationship: Para criar o "link" mágico entre as tabelas (ex: uma Tabela tem muitas Colunas).
# sessionmaker: Para criar sessões de comunicação com o banco de dados.
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Importa o caminho do nosso banco de dados SQLite definido no arquivo de configuração.
from .config import DATABASE_PATH

# Cria uma classe 'Base' da qual todos os nossos modelos de tabela irão herdar.
Base = declarative_base()


class EsquemasCatalogados(Base):
    """
    Representa a tabela 'esquemas_catalogados' no nosso banco de dados do catálogo.
    Esta tabela armazena os nomes dos schemas do banco de dados original (ex: 'public', 'dw').
    """
    # Define o nome da tabela no banco de dados.
    __tablename__ = 'esquemas_catalogados'
    
    # Define as colunas desta tabela.
    id = Column(Integer, primary_key=True)
    nome = Column(String(200), unique=True, nullable=False)
    
    # Define o relacionamento com a tabela 'TabelasCatalogadas'.
    # Isso nos permite acessar todas as tabelas de um schema usando 'meu_esquema.tabelas'.
    # 'back_populates' cria o link de volta, permitindo que acessemos 'minha_tabela.esquema'.
    # 'cascade' garante que, se um schema for deletado, todas as suas tabelas também sejam.
    tabelas = relationship('TabelasCatalogadas', back_populates='esquema', cascade="all, delete-orphan")


class TabelasCatalogadas(Base):
    """
    Representa a tabela 'tabelas_catalogadas' no nosso banco de dados do catálogo.
    Armazena informações sobre cada tabela ou view extraída do banco original.
    """
    __tablename__ = 'tabelas_catalogadas'
    
    # --- Colunas que vêm do banco de dados original 
    id = Column(Integer, primary_key=True)
    nome_fisico = Column(String(200), nullable=False)
    tipo_objeto = Column(String(50), nullable=False)
    
    # --- Colunas que serão preenchidas por nós através da interface (a curadoria)
    nome_negocio = Column(String(200))
    descricao = Column(Text)
    
    # --- Definição das Chaves Estrangeiras e Relacionamentos 
    # Define que esta tabela pertence a um EsquemaCatalogado.
    schema_id = Column(Integer, ForeignKey('esquemas_catalogados.id'), nullable=False) 
    
    # Cria o relacionamento de volta para a classe EsquemasCatalogados.
    esquema = relationship('EsquemasCatalogados', back_populates='tabelas')
    
    # Cria o relacionamento com a tabela 'ColunasCatalogadas'.
    # Permite acessar todas as colunas de uma tabela usando 'minha_tabela.colunas'.
    colunas = relationship('ColunasCatalogadas', back_populates='tabela', cascade="all, delete-orphan") 


class ColunasCatalogadas(Base):
    """
    Representa a tabela 'colunas_catalogadas' no nosso banco de dados do catálogo.
    Armazena informações sobre cada coluna de cada tabela.
    """
    __tablename__ = 'colunas_catalogadas'

    # --- Colunas que vêm do banco de dados original
    id = Column(Integer, primary_key=True)
    nome_fisico = Column(String(200), nullable=False)
    tipo_dado = Column(String(100))
    nulo = Column(Boolean)
    pk = Column(Boolean)

    # --- Colunas que serão preenchidas por nós através da interface (a curadoria)
    nome_negocio = Column(String(200))
    descricao = Column(Text)
    
    # --- Definição da Chave Estrangeira e Relacionamento
    # Define que esta coluna pertence a uma TabelaCatalogada.
    tabela_id = Column(Integer, ForeignKey('tabelas_catalogadas.id'), nullable=False) 
    
    # Cria o relacionamento de volta para a classe TabelasCatalogadas.
    tabela = relationship('TabelasCatalogadas', back_populates='colunas') 


# --- Funções Auxiliares de Conexão
def get_engine():
    """
    Cria e retorna uma 'engine' do SQLAlchemy.
    """
    return create_engine(f"sqlite:///{DATABASE_PATH}")


def get_session():
    """
    Cria uma nova sessão de comunicação com o banco de dados.
    """
    engine = get_engine()
    
    # Este comando crucial irá ler as classes e criar as tabelas com os nomes corretos.
    Base.metadata.create_all(engine)
    
    # Cria uma "fábrica" de sessões ligada à nossa engine.
    Session = sessionmaker(bind=engine)
    
    # Retorna uma nova instância da sessão, pronta para ser usada.
    return Session()