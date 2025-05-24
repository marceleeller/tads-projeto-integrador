import enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime 
from werkzeug.security import generate_password_hash, check_password_hash

# Inicializa o objeto SQLAlchemy.
db = SQLAlchemy()

# --- Enums ---
class StatusProduto(enum.Enum):
    NOVO = 'NOVO'
    USADO = 'USADO'

class StatusSolicitacao(enum.Enum):
    PROCESSANDO = 'PROCESSANDO'
    PENDENTE = 'PENDENTE'
    APROVADA = 'APROVADA'
    RECUSADA = 'RECUSADA'
    CANCELADA = 'CANCELADA'

class TipoDeInterese(enum.Enum):
    TROCA = 1
    DOAÇÃO = 2

# --- Modelos ---

class Imagem(db.Model):
    __tablename__ = 'imagem'
    id_imagem = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url_imagem = db.Column(db.String(200), nullable=False)
    descricao_imagem = db.Column(db.String(100), nullable=True)
    id_produto = db.Column(db.Integer, db.ForeignKey('produto.id_produto'), nullable=False)
    # O atributo 'produto_obj' (ou 'produto') será criado pelo backref de Produto.imagens

    def to_dict(self):
        return {
            'id_imagem': self.id_imagem,
            'url_imagem': self.url_imagem,
            'descricao_imagem': self.descricao_imagem
        }

    def __repr__(self) -> str:
        return f"<Imagem(id={self.id_imagem}, url='{self.url_imagem[:30]}...')>"

class Categoria(db.Model):
    __tablename__ = 'categoria'
    id_categoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_categoria = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    # O atributo 'produtos' será criado pelo backref de Produto.categorias

    def to_dict(self):
        return {
            'id_categoria': self.id_categoria,
            'nome_categoria': self.nome_categoria,
            'descricao': self.descricao
        }

    def __repr__(self) -> str:
        return f"<Categoria(id={self.id_categoria}, nome='{self.nome_categoria}')>"

tabela_produto_categoria = db.Table(
    'produto_categoria',
    db.Column('id_produto', db.ForeignKey('produto.id_produto', ondelete='CASCADE'), primary_key=True),
    db.Column('id_categoria', db.ForeignKey('categoria.id_categoria', ondelete='CASCADE'), primary_key=True)
)

class Produto(db.Model):
    __tablename__ = 'produto'
    id_produto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_produto = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categoria.id_categoria'))
    status = db.Column(db.Enum(StatusProduto), nullable=False, default=StatusProduto.NOVO)  # <-- Adicionado
    quantidade = db.Column(db.Integer, nullable=False, default=1)  # <-- Adicionado

    # Relacionamentos
    imagens = db.relationship("Imagem", backref="produto", lazy="selectin", cascade="all, delete-orphan")
    categoria = db.relationship("Categoria", foreign_keys=[id_categoria])

    # Relacionamento explícito com Usuario (proprietário do produto)
    proprietario = db.relationship("Usuario", back_populates="produtos")

    def to_dict(self, include_owner=False, include_categoria=True, include_imagens=True):
        data = {
            'id_produto': self.id_produto,
            'nome_produto': self.nome_produto,
            'descricao': self.descricao,
            'id_usuario': self.id_usuario,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'status': self.status.value if self.status else None,           # <-- Adicionado
            'quantidade': self.quantidade                                   # <-- Adicionado
        }
        if include_owner and self.proprietario:
            data['proprietario_details'] = self.proprietario.to_dict_simple()
        
        if include_categoria and self.categoria:
            data['categoria'] = self.categoria.to_dict()
        
        if include_imagens:
            data['imagens'] = [img.to_dict() for img in self.imagens]
        return data

    def __repr__(self) -> str:
        return f"<Produto(id={self.id_produto}, nome='{self.nome_produto}')>"

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_usuario = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column('senha', db.String(250), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relacionamentos
    enderecos_usuario = db.relationship("EnderecoUsuario", backref="usuario", lazy="dynamic", cascade="all, delete-orphan")
    
    # Relacionamento explícito com Produto
    produtos = db.relationship("Produto", back_populates="proprietario", lazy="dynamic")
    
    solicitacoes_feitas = db.relationship("Solicitacao", foreign_keys="Solicitacao.id_usuario_solicitante", backref="usuario_solicitante_obj", lazy="dynamic")
    mensagens_enviadas = db.relationship("Mensagem", foreign_keys="Mensagem.id_usuario", backref="usuario_obj", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'nome_usuario': self.nome_usuario,
            'email': self.email,
            'cpf': self.cpf,
            'telefone': self.telefone,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None
        }
    
    def to_dict_simple(self):
        return {
            'id_usuario': self.id_usuario,
            'nome_usuario': self.nome_usuario
        }

    def get_id(self):
        return str(self.id_usuario)

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
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)

    def to_dict(self):
        return {
            'id_endereco': self.id_endereco,
            'cep': self.cep,
            'bairro': self.bairro,
            'rua': self.rua,
            'numero': self.numero,
            'complemento': self.complemento,
            'cidade': self.cidade,
            'estado': self.estado,
            'id_usuario': self.id_usuario
        }

    def __repr__(self) -> str:
        return f"<EnderecoUsuario(id={self.id_endereco}, cep='{self.cep}', cidade='{self.cidade}')>"

class Mensagem(db.Model):
    __tablename__ = 'mensagem'
    id_mensagem = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conteudo_mensagem = db.Column(db.String(500), nullable=False)
    data_envio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_solicitacao = db.Column(db.Integer, db.ForeignKey('solicitacao.id_solicitacao'), nullable=False)
    # O atributo 'usuario_obj' será criado pelo backref de Usuario.mensagens_enviadas
    # O atributo 'solicitacao_obj' será criado pelo backref de Solicitacao.mensagens

    def to_dict(self):
        return {
            'id_mensagem': self.id_mensagem,
            'conteudo_mensagem': self.conteudo_mensagem,
            'id_usuario': self.id_usuario,
            'nome_remetente': self.usuario_obj.nome_usuario if self.usuario_obj else None,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None
        }

    def __repr__(self) -> str:
        return f"<Mensagem(id={self.id_mensagem}, data='{self.data_envio}')>"

class Transacao(db.Model):
    __tablename__ = 'transacao'
    id_transacao = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data_transacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # O atributo 'solicitacao' será criado pelo backref de Solicitacao.transacao_obj (uselist=False)

    def to_dict(self):
        return {
            'id_transacao': self.id_transacao,
            'data_transacao': self.data_transacao.isoformat() if self.data_transacao else None
        }

    def __repr__(self) -> str:
        return f"<Transacao(id={self.id_transacao}, data='{self.data_transacao}')>"

class Solicitacao(db.Model):
    __tablename__ = 'solicitacao'
    id_solicitacao = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(db.Enum(StatusSolicitacao), nullable=False, default=StatusSolicitacao.PENDENTE)
    data_solicitacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_usuario_solicitante = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_produto_desejado = db.Column(db.Integer, db.ForeignKey('produto.id_produto'), nullable=False)
    id_produto_ofertado = db.Column(db.Integer, db.ForeignKey('produto.id_produto'), nullable=True)
    id_transacao = db.Column(db.Integer, db.ForeignKey('transacao.id_transacao'), nullable=True)  # <-- Adicionado

    # Relacionamentos
    produto_desejado_obj = db.relationship("Produto", foreign_keys=[id_produto_desejado], backref="solicitacoes_para_este_produto")
    produto_ofertado_obj = db.relationship("Produto", foreign_keys=[id_produto_ofertado], backref="solicitacoes_onde_foi_ofertado")
    transacao_obj = db.relationship("Transacao", backref=db.backref("solicitacoes", lazy="dynamic"))  # <-- Corrigido
    mensagens = db.relationship("Mensagem", backref="solicitacao_obj", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_produtos_details=False):
        data = {
            'id_solicitacao': self.id_solicitacao,
            'status': self.status.value if self.status else None,
            'data_solicitacao': self.data_solicitacao.isoformat() if self.data_solicitacao else None,
            'id_usuario_solicitante': self.id_usuario_solicitante,
            'id_produto_desejado': self.id_produto_desejado,
            'id_produto_ofertado': self.id_produto_ofertado,
            'id_transacao': self.id_transacao
        }
        if hasattr(self, 'usuario_solicitante_obj') and self.usuario_solicitante_obj:
             data['usuario_solicitante'] = self.usuario_solicitante_obj.to_dict_simple()

        if include_produtos_details:
            if self.produto_desejado_obj:
                data['produto_desejado'] = self.produto_desejado_obj.to_dict()
            if self.produto_ofertado_obj:
                data['produto_ofertado'] = self.produto_ofertado_obj.to_dict()
        
        if self.produto_desejado_obj and self.produto_desejado_obj.categoria:
            data['tipo_solicitacao'] = self.produto_desejado_obj.categoria.nome_categoria

        return data

    def __repr__(self) -> str:
        return f"<Solicitacao(id={self.id_solicitacao}, status='{self.status.value}')>"