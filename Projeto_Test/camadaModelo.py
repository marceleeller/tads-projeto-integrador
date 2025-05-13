# backEnd.py

import enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin # Necessário para o modelo Usuario
from werkzeug.security import generate_password_hash, check_password_hash # Importado para a rota de registro
from datetime import datetime, date # Necessário para tipos de data/datetime

# Inicializa o objeto SQLAlchemy. Ele será associado à instância do Flask depois.
db = SQLAlchemy()

# --- Definição de Enums para os Tipos de Status ---

class Disponibilidade (enum.Enum):
    DISPONIVEL = "DISPONIVEL"
    EM_NEGOCIACAO = "EM NEGOCIAÇÃO"
    NEGOCIACAO_ENCERRADA = "NEGOCIAÇÃO ENCERRADA"

class StatusProduto(enum.Enum):
    NOVO = 'NOVO'
    USADO = 'USADO'

class StatusSolicitacao(enum.Enum):
    PENDENTE = 'PENDENTE'
    APROVADA = 'APROVADA'
    RECUSADA = 'RECUSADA'

class TipoDeInterese(enum.Enum):
    TROCA = 'TROCA'
    DOAÇÃO = 'DOAÇÃO'

# --- Definição dos Modelos do Banco de Dados ---

class Imagem(db.Model):
    __tablename__ = 'imagem'
    id_imagem = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url_imagem = db.Column(db.String(200), nullable=False)
    descricao_imagem = db.Column(db.String(100), nullable=True)
    id_produto = db.Column(db.Integer, db.ForeignKey('produto.id_produto'), nullable=False)

    def __repr__(self) -> str:
        return f"<Imagem(id={self.id_imagem}, url='{self.url_imagem[:30]}...')>"

class Categoria(db.Model):
    __tablename__ = 'categoria'
    id_categoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_categoria = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(80), nullable=False)
    # Relacionamento de volta definido em Produto usando secondary

    def __repr__(self) -> str:
        return f"<Categoria(id={self.id_categoria}, nome='{self.nome_categoria}')>"

# Tabela de associação para Relação Muitos-para-Muitos entre Produto e Categoria
tabela_produto_categoria = db.Table(
    'produto_categoria',
    db.Column('id_produto', db.ForeignKey('produto.id_produto'), primary_key=True),
    db.Column('id_categoria', db.ForeignKey('categoria.id_categoria'), primary_key=True)
)

class Produto(db.Model):
    __tablename__ = 'produto'
    id_produto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_produto = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    interesse = db.Column(db.Enum(TipoDeInterese), nullable=False)
    disponibilidade = db.column(db.Enum(Disponibilidade), nullable=False)
    data_cadastro = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.Enum(StatusProduto), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=True)

    # Relacionamentos
    imagens = db.relationship("Imagem", backref="produto", lazy="dynamic")
    categorias = db.relationship("Categoria", secondary=tabela_produto_categoria, backref="produtos", lazy="dynamic") # Corrigido backref para "produtos"

    def __repr__(self) -> str:
        return f"<Produto(id={self.id_produto}, nome='{self.nome_produto}', status='{self.status.value}')>"

class Usuario(UserMixin, db.Model): # Herda de UserMixin para Flask-Login
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_usuario = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True) # CPF pode ser nulo? Verifique sua regra de negócio.
    telefone = db.Column(db.String(14), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(150), db.String(250), nullable=False) # Armazenaremos o hash da senha aqui, mapeando para a coluna 'senha'
    data_nascimento = db.Column(db.Date, nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # confirme_a_sua_senha NÃO deve ser uma coluna no banco. É apenas para validação na entrada de dados.
    # Relacionamentos
    enderecos_usuario = db.relationship("EnderecoUsuario", backref="usuario", lazy="dynamic")
    produtos = db.relationship("Produto", backref="usuario", lazy="dynamic")
    mensagens = db.relationship("Mensagem", backref="usuario", lazy="dynamic")
    solicitacoes = db.relationship("Solicitacao", backref="usuario", lazy="dynamic")
    
    def definir_senha(self, password):
        # Gera o hash da senha. O método padrão inclui salting.
        self.senha_hash = generate_password_hash(password)

    def verificar_senha(self, password):
       # Compara a senha fornecida com o hash armazenado
        is_valid = check_password_hash(self.senha_hash, password)
        if not is_valid:
             print ("Tentativa de senha incorreta para o usuário {self.email}.")
        return is_valid

    # --- Representação do Objeto (Opcional, útil para debug) ---
    def __repr__(self):
        return f"<Usuario {self.email}>"
        


class EnderecoUsuario(db.Model):
    __tablename__ = 'endereco_usuario'
    id_endereco = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cep = db.Column(db.String(9), nullable=False)
    bairro = db.Column(db.String(80), nullable=False)
    rua = db.Column(db.String(80), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    complemento = db.Column(db.String(150), nullable=True)
    cidade = db.Column(db.String(80), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False) # Chave estrangeira
    # Relacionamento de volta definido em Usuario

    def __repr__(self) -> str:
        return f"<EnderecoUsuario(id={self.id_endereco}, cep='{self.cep}', cidade='{self.cidade}')>"

class Mensagem(db.Model):
    __tablename__ = 'mensagem'
    id_mensagem = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conteudo_mensagem = db.Column(db.String(100), nullable=False)
    data_envio = db.Column(db.Date, nullable=False, default=date.today)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False) # Chave estrangeira

    def __repr__(self) -> str:
        return f"<Mensagem(id={self.id_mensagem}, data='{self.data_envio}')>"

class Transacao(db.Model):
    __tablename__ = 'transacao'
    id_transacao = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data_transacao = db.Column(db.Date, nullable=False, default=date.today)
    # Relacionamento
    solicitacoes = db.relationship("Solicitacao", backref="transacao", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Transacao(id={self.id_transacao}, data='{self.data_transacao}')>"


class Solicitacao(db.Model):
    __tablename__ = 'solicitacao'
    id_solicitacao = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(db.Enum(StatusSolicitacao), nullable=False)
    data_solicitacao = db.Column(db.Date, nullable=False, default=date.today)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False) # Chave estrangeira
    id_transacao = db.Column(db.Integer, db.ForeignKey('transacao.id_transacao'), nullable=False) # Chave estrangeira

    def __repr__(self) -> str:
        return f"<Solicitacao(id={self.id_solicitacao}, status='{self.status.value}')>"

# Não coloque db.init_app(app) ou a execução do app aqui.
# Isso deve ser feito em app.py.