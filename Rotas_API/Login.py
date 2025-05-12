# Importa as bibliotecas e módulos necessários
from flask import Flask, request, jsonify, redirect, url_for
from werkzeug.security import check_password_hash
import pymysql # Importa pymysql para garantir compatibilidade com Flask-SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # Importa componentes do Flask-Login
from camadaModelo import db, Usuario
pymysql.install_as_MySQLdb()

# Cria a instância da aplicação Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_padrao_ou_config_MUDE_ISSO'

# Configurações do banco de dados MySQL
# ATENÇÃO: Substitua os placeholders pelas suas credenciais REAIS do banco de dados!
DB_USER = 'seu_usuario_mysql'
DB_PASSWORD = 'sua_senha_mysql'
DB_HOST = 'localhost' # Ou o endereço do seu servidor MySQL (ex: '127.0.0.1', nome do serviço Docker)
DB_PORT = 3306 # Porta padrão do MySQL
DB_NAME = 'seu_banco_de_dados'

# Constrói a string de conexão do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recomendado para evitar avisos

# --- Inicializa as Extensões ---
# Associa o objeto 'db' (inicializado no seu arquivo de modelos) à instância do app
if db: # Verifica se 'db' foi importado com sucesso
    db.init_app(app)
    print("Flask-SQLAlchemy inicializado com o app.")
else:
     print("Aviso: Flask-SQLAlchemy não foi inicializado devido a erro na importação do 'db'.")

# Inicializa o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# Define a view para onde o usuário será redirecionado se tentar acessar uma rota protegida sem estar logado.
# Neste caso, como é uma API, podemos retornar um JSON de erro em vez de redirecionar.
# Vamos definir uma função para lidar com isso.
# login_manager.login_view = 'login' # Descomente e ajuste se usar templates HTML

# --- Funções de Callback do Flask-Login ---

@login_manager.user_loader
def load_user(usuario_id):
    """
    Callback usado pelo Flask-Login para carregar um usuário a partir do seu ID.
    Este ID é armazenado na sessão.
    Retorna o objeto Usuario correspondente ao ID, ou None se o usuário não for encontrado.
    """
    if Usuario: # Verifica se o modelo Usuario foi importado
        # O ID armazenado na sessão pelo Flask-Login é uma string, então convertemos para int
        return Usuario.query.get(int(usuario_id))
    return None

@login_manager.unauthorized_handler
def unauthorized():
    """
    Handler chamado pelo Flask-Login quando um usuário não autenticado tenta acessar
    uma rota protegida por @login_required.
    Neste caso de API, retornamos um JSON de erro 401.
    """
    return jsonify({'erro': 'Autenticação necessária para acessar este recurso.'}), 401


# --- Definição das Rotas da API ---

@app.route('/login', methods=['POST'])
def login():

    # Obtém os dados JSON da requisição
    data = request.get_json()
    
    """
    Endpoint para autenticar um usuário.
    Espera um corpo de requisição JSON com 'email' e 'senha'.
    Se a autenticação for bem-sucedida, loga o usuário usando Flask-Login.
    Retorna uma resposta JSON indicando sucesso ou falha.
    """
    # Se o usuário já estiver autenticado, podemos redirecionar ou retornar uma mensagem
    if current_user.is_authenticated:
        return jsonify({'mensagem': 'Usuário já autenticado.'}), 200

    # Valida se os campos 'email' e 'senha' estão presentes no JSON
    if not data or 'email' not in data or 'senha' not in data:
        return jsonify({'erro': 'Email e senha são obrigatórios.'}), 400 # Bad Request

    email_ = data['email']
    senha = data['senha']

    # Verifica se o modelo Usuario foi importado antes de tentar usá-lo
    if not Usuario:
        return jsonify({'erro': 'Erro interno: Modelo de usuário não carregado.'}), 500 # Internal Server Error

    try:
        # Busca o usuário no banco de dados pelo email. Assume que o email é único.
        usuario = Usuario.query.filter_by(email=email_).first()

        # Verifica se o usuário foi encontrado E se a senha fornecida corresponde ao hash armazenado
        if usuario and check_password_hash(usuario.password_hash, senha):
            # Autenticação bem-sucedida
            # Usa login_user() do Flask-Login para logar o usuário na sessão
            login_user(usuario) # Opcional: remember=True para funcionalidade "Lembrar-me"

            # Retorna uma resposta 200 (OK) com dados básicos do usuário
            return jsonify({
                'mensagem': 'Autenticação bem-sucedida',
                'id_usuario': usuario.id_usuario,
                'nome_usuario': usuario.nome_usuario,
                'email': usuario.email
            }), 200
        else:
            # Usuário não encontrado ou senha incorreta
            return jsonify({'erro': 'Email ou senha inválidos.'}), 401 # Unauthorized

    except Exception as e:
        print(f"Erro ao autenticar usuário: {e}")
        return jsonify({'erro': 'Ocorreu um erro interno ao tentar autenticar.'}), 500

''''
# Esta rota só pode ser acessada por usuários autenticados
@app.route('/logout', methods=['POST'])
@login_required # Esta rota só pode ser acessada por usuários autenticados
def logout():
    """
    Endpoint para deslogar o usuário autenticado.
    Usa logout_user() do Flask-Login.
    """
    logout_user()
    return jsonify({'mensagem': 'Usuário deslogado com sucesso.'}), 200
'''

'''
@app.route('/protected', methods=['GET'])
@login_required # Este decorador garante que apenas usuários autenticados podem acessar esta rota
def protected_route():
    """
    Endpoint de exemplo que só pode ser acessado por usuários autenticados.
    Demonstra o uso do decorador @login_required.
    """
    # current_user é fornecido pelo Flask-Login e representa o usuário logado
    return jsonify({
        'mensagem': f'Olá, {current_user.nome_usuario}! Você acessou uma rota protegida.',
        'id_usuario': current_user.id_usuario
    }), 200
'''


# --- Execução da Aplicação ---
# Este bloco de execução é útil para rodar este script diretamente para testes.
# Em uma aplicação maior, a execução principal geralmente fica em um arquivo 'app.py'
# que importa e registra esta API.
if __name__ == '__main__':
    if db: # Verifica se 'db' foi inicializado
        with app.app_context():
            try:
                db.create_all()
                print("Banco de dados conectado e tabelas verificadas/criadas.")
            except Exception as e:
                print(f"Erro fatal ao conectar ou criar tabelas do MySQL: {e}")
    else:
        print("Aviso: db.create_all() não foi executado porque 'db' não foi inicializado.")

    print("Iniciando o servidor Flask com Flask-Login...")
    app.run(debug=True, host='0.0.0.0', port=5000)
