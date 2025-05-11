import enum
from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, g # Importar g para contexto da requisição
from flask_sqlalchemy import SQLAlchemy # Usaremos Flask-SQLAlchemy para gerenciar o DB no Flask
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date # Importar para exemplos de data/datetime
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required # Importações mais completas de Flask-Login

# Inicializa o Flask e configura a SECRET_KEY
# SUBSTITUA 'sua_chave_secreta_padrao_ou_config' POR UMA CHAVE ALEATÓRIA LONGA E SEGURA EM PRODUÇÃO!
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_padrao_ou_config'
# Configurações do banco de dados (use variáveis de ambiente ou arquivo de configuração real!)
# Exemplo de URL para MySQL com pymysql:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://seu_usuario:sua_senha@seu_host:sua_porta/seu_banco'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecotroca.db' # Exemplo com SQLite para rodar facilmente
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desabilita rastreamento de modificações (recomendado)


# Inicializa a extensão Flask-SQLAlchemy
# 'db' será o nosso objeto central para interagir com o banco de dados
db = SQLAlchemy(app)

# Inicializa o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Define a view para redirecionar usuários não autenticados

# Define Enums Python para os tipos ENUM do banco de dados
# Mantemos as classes Python, mas usaremos db.Enum no mapeamento das colunas
class StatusProduto(enum.Enum):
    NOVO = 'NOVO'
    USADO = 'USADO'

class StatusSolicitacao(enum.Enum):
    PENDENTE = 'PENDENTE'
    APROVADA = 'APROVADA'
    RECUSADA = 'RECUSADA'


class Imagem(db.Model): 
    __tablename__ = 'imagem'

    id_imagem = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    url_imagem = db.Column(db.String(200), nullable=False)
    descricao_imagem = db.Column(db.String(100), nullable=True)
    # Chave estrangeira
    id_produto = db.Column(db.Integer, db.ForeignKey('produto.id_produto'), nullable=False)

    def __repr__(self) -> str:
        return f"<Imagem(id={self.id_imagem}, url='{self.url_imagem[:30]}...')>"

class Categoria(db.Model): 
    __tablename__ = 'categoria'

    id_categoria = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    nome_categoria = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(80), nullable=False)

    # O relacionamento de volta 'produtos' está definido na classe Produto com backref

    def __repr__(self) -> str:
        return f"<Categoria(id={self.id_categoria}, nome='{self.nome_categoria}')>"
    
# Tabela de associação para Relação Muitos-para-Muitos entre Produto e Categoria
# Usamos db.Table em vez de apenas Table
tabela_produto_categoria = db.Table(
    'produto_categoria',
    db.Column('id_produto', db.ForeignKey('produto.id_produto'), primary_key=True),
    db.Column('id_categoria', db.ForeignKey('categoria.id_categoria'), primary_key=True)
)

class Produto(db.Model): # Herda de db.Model
    __tablename__ = 'produto'

    id_produto = db.Column(db.Integer, primary_key=True, autoincrement=True) # Use db.Column
    nome_produto = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Enum(StatusProduto), nullable=False) # Use db.Enum
    data_cadastro = db.Column(db.Date, nullable=False, default=date.today) # Sugestão: Usar default=date.today
    quantidade = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=True) # Use db.Numeric
    # Chaves estrangeiras (usando db.ForeignKey)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    # Relacionamentos
    # Os backrefs 'usuario' e 'endereco_produto' estão definidos nas classes correspondentes
    imagens = db.relationship("Imagem", backref="produto", lazy="dynamic")
    categorias = db.relationship("Categoria", secondary=tabela_produto_categoria, backref="produto", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Produto(id={self.id_produto}, nome='{self.nome_produto}', status='{self.status.value}')>"


class Usuario(UserMixin, db.Model): 
    __tablename__ = 'usuario'

    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    nome_usuario = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    telefone = db.Column(db.String(14), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(250), nullable=False) 
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Sugestão: Usar default=datetime.utcnow
    data_nascimento = db.Column(db.Date, nullable=False)
    # Relacionamentos 
    enderecos_usuario = db.relationship("EnderecoUsuario", backref="usuario", lazy="dynamic") # lazy="dynamic" pode ser útil para consultas filtradas
    produtos = db.relationship("Produto", backref="usuario", lazy="dynamic")
    mensagens = db.relationship("Mensagem", backref="usuario", lazy="dynamic")
    solicitacoes = db.relationship("Solicitacao", backref="usuario", lazy="dynamic")

    # Métodos para segurança (hashing de senha e compatibilidade com Flask-Login)
    def set_password(self, password):
        """Define a senha do usuário, armazenando um hash."""
        self.senha = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.senha, password)

    # Método requerido pelo Flask-Login para obter o ID do usuário como string
    # Já fornecido por UserMixin, mas você pode sobrescrever se precisar
    def get_id(self):
        return str(self.id_usuario)

    def __repr__(self) -> str:
        return f"<Usuario(id={self.id_usuario}, nome='{self.nome_usuario}', email='{self.email}')>"


class EnderecoUsuario(db.Model): # Herda de db.Model
    __tablename__ = 'endereco_usuario'

    id_endereco = db.Column(db.Integer, primary_key=True, autoincrement=True) # Use db.Column
    cep = db.Column(db.String(9), nullable=False)
    bairro = db.Column(db.String(80), nullable=False)
    rua = db.Column(db.String(80), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    complemento = db.Column(db.String(150), nullable=True)
    cidade = db.Column(db.String(80), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    # Chave estrangeira (usando db.ForeignKey)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)


    def __repr__(self) -> str:
        return f"<EnderecoUsuario(id={self.id_endereco}, cep='{self.cep}', cidade='{self.cidade}')>"


class Mensagem(db.Model): 
    __tablename__ = 'mensagem'

    id_mensagem = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    conteudo_mensagem = db.Column(db.String(100), nullable=False)
    data_envio = db.Column(db.Date, nullable=False, default=date.today) # Sugestão: Usar default=date.today
    # Chave estrangeira
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)

    def __repr__(self) -> str:
        return f"<Mensagem(id={self.id_mensagem}, data='{self.data_envio}')>"

class Solicitacao(db.Model): # Herda de db.Model
    __tablename__ = 'solicitacao'

    id_solicitacao = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    status = db.Column(db.Enum(StatusSolicitacao), nullable=False) 
    data_solicitacao = db.Column(db.Date, nullable=False, default=date.today)
    # Chaves estrangeiras
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_transacao = db.Column(db.Integer, db.ForeignKey('transacao.id_transacao'), nullable=False)

    def __repr__(self) -> str:
        return f"<Solicitacao(id={self.id_solicitacao}, status='{self.status.value}')>"

class Transacao(db.Model): 
    __tablename__ = 'transacao'

    id_transacao = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    data_transacao = db.Column(db.Date, nullable=False, default=date.today) 
    
    solicitacoes = db.relationship("Solicitacao", backref="transacao", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Transacao(id={self.id_transacao}, data='{self.data_transacao}')>"




# --- Implementação da função user_loader para Flask-Login ---
# Esta função é usada pelo Flask-Login para carregar um usuário a partir do ID armazenado na sessão
@login_manager.user_loader
def load_user(user_id):
    # Use a sessão do Flask-SQLAlchemy (db.session) para obter o usuário
    if user_id is not None:
        # Use db.session.get() para buscar pelo PK, garantindo que user_id seja int
        try:
            return db.session.get(Usuario, int(user_id))
        except (ValueError, TypeError):
            # user_id não é um inteiro válido
            return None
    return None

# --- Exemplos de como usar (agora com Flask-SQLAlchemy) ---

# Para criar as tabelas dentro do contexto da aplicação Flask:
# with app.app_context():
#    db.create_all() # Use db.create_all() em vez de Base.metadata.create_all()

# Para criar um novo usuário com senha segura e adicionar ao DB:
# with app.app_context():
#     novo_usuario = Usuario(
#         nome_usuario="Usuário Flask-SQLAlchemy",
#         telefone="9876543210",
#         email="flask_sa@exemplo.com",
#         data_cadastro=datetime.now(),
#         data_nascimento=date(1990, 5, 15)
#     )
#     novo_usuario.set_password("senha_segura_flask_sa")
#     db.session.add(novo_usuario)
#     db.session.commit()
#     print("Novo usuário criado com sucesso!")

# Para verificar uma senha durante o login e autenticar (em uma rota Flask):
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form.get('email')
#         password = request.form.get('password')
#         usuario = db.session.filter_by(email=email).first() # Use db.session para consultas
#         if usuario and usuario.check_password(password):
#             login_user(usuario) # Autentica o usuário usando Flask-Login
#             flash('Login bem-sucedido!', 'success')
#             # Redirecionar para a página desejada após o login
#             next_page = request.args.get('next') or url_for('index') # Exemplo de redirecionamento
#             return redirect(next_page)
#         else:
#             flash('Email ou senha inválidos.', 'danger')
#     # Renderizar formulário de login para requisições GET
#     return render_template('login.html') # Assumindo que você tem um template login.html

# Exemplo de rota protegida por login:
# @app.route('/perfil')
# @login_required # Requer que o usuário esteja logado
# def perfil():
#     # current_user contém o objeto do usuário logado
#     return f'Olá, {current_user.nome_usuario}! Seu ID é {current_user.id_usuario}.'

# Exemplo de rota de logout:
# @app.route('/logout')
# @login_required # Opcional, mas faz sentido que apenas logados possam fazer logout
# def logout():
#     logout_user() # Faz logout do usuário atual
#     flash('Você saiu da sua conta.', 'info')
#     return redirect(url_for('index')) # Redirecionar para a página inicial ou login

# # Exemplo de rota inicial (placeholder)
# @app.route('/')
# def index():
#    # Obter mensagens flash
#    messages = get_flashed_messages(with_categories=True)
#    return render_template('index.html', messages=messages) # Assumindo index.html pode exibir mensagens

# Se você estiver rodando este arquivo diretamente para testes:
# if __name__ == '__main__':
#    with app.app_context():
#        db.create_all() # Cria as tabelas se não existirem ao rodar o script
#    # app.run(debug=True) # Rode o aplicativo Flask (descomente para testar a aplicação web)