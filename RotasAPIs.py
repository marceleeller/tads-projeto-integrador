# app.py

import pymysql
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, get_flashed_messages, g
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from datetime import datetime, date 
from camadaModelo import db, Usuario, EnderecoUsuario, StatusProduto, StatusSolicitacao # Importe todas as classes de modelo e enums que usar

pymysql.install_as_MySQLdb()
app = Flask(__name__)


# SUBSTITUA 'sua_chave_secreta_padrao_ou_config' POR UMA CHAVE ALEATÓRIA LONGA E SEGURA EM PRODUÇÃO!
app.config['SECRET_KEY'] = 'sua_chave_secreta_padrao_ou_config_MUDE_ISSO' # Use uma chave segura!

# Configurações do banco de dados MySQL
DB_USER = ''
DB_PASSWORD = '1'
DB_HOST = '' # <-- Mude para o endereço real do seu servidor MySQL (ex: '127.0.0.1' ou o nome do serviço Docker)
DB_PORT = ''
DB_NAME = ''

# Construindo a string de conexão do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recomendado

# --- Inicializa as Extensões ---
# Associa o objeto 'db' inicializado em backEnd.py à instância do app
db.init_app(app)
login_manager = LoginManager(app)

# Configurações do Flask-Login
login_manager.login_view = 'login_route' # Define a view (rota) para redirecionar usuários não autenticados (use o nome da função da rota)
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# --- Funções Auxiliares ---
# Função para carregar um usuário do banco de dados, necessária para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """
    Carrega um usuário a partir do ID do usuário armazenado na sessão.
    Usado pelo Flask-Login.
    """
    if user_id is not None:
        try:
            # Usa o objeto 'db' e o modelo 'Usuario' importados de backEnd.py
            return db.session.get(Usuario, int(user_id)) # Forma recomendada de buscar por PK
        except (ValueError, TypeError):
            # user_id não é um inteiro válido ou None
            return None
    return None


# --- Definição das Rotas da Aplicação ---

@app.route('/')
def index():
    # Renderiza o template que contém a lista E o formulário de cadastro
    # Certifique-se de que o template esteja em 'templates/cadastro.html'
    return render_template("cadastro.html") # Remova 'templates\' se a pasta 'templates' estiver na raiz do projeto

# Rota para registro de Usuario
@app.route('/Registro', methods=['POST'])
def register():
    # Espera um JSON no corpo da requisição
    data = request.get_json()

    # Validações (verifique se todos os campos obrigatórios existem em 'data')
    if not all(key in data for key in ['nome', 'cpf', 'telefone', 'email', 'senha', 'cep', 'bairro', 'rua', 'numero', 'cidade', 'estado', 'data_nascimento']):
         return jsonify({'Erro': 'Campos obrigatórios faltando'}), 400

    # Validação de senhas (apenas na entrada de dados, não armazene confirme_a_sua_senha no DB)
    # if data.get('senha') != data.get('confirme_a_sua_senha'): # Você não forneceu confirme_a_sua_senha no JSON de entrada
    #     return jsonify({'Erro': 'As senhas não coincidem'}), 400


    # Verifica se o email já existe
    user_email = Usuario.query.filter_by(email=data['email']).first()
    if user_email:
        return jsonify({'Erro': 'Email já foi registrado'}), 400

    # Verifica se o CPF já existe (verifique se o CPF é obrigatório na sua regra de negócio)
    if 'cpf' in data and data['cpf']: # Verifica se 'cpf' está no JSON e não é vazio
        user_cpf = Usuario.query.filter_by(cpf=data['cpf']).first()
        if user_cpf:
             return jsonify({'Erro': 'CPF já registrado'}), 400


    # Cria uma nova instância de Usuario
    novo_usuario = Usuario(
        nome_usuario=data['nome'], # Verifique o nome do campo no modelo (nome_usuario vs nome)
        cpf=data.get('cpf'), # Use .get() para campos opcionais ou que podem não estar sempre presentes
        telefone=data['telefone'],
        email=data['email'],
        data_nascimento=datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date() # Converte string para data (ajuste o formato se necessário)
        # 'senha' NÃO é atribuída diretamente, usamos set_password abaixo
    )
    # Define a senha usando o método do modelo para gerar o hash
    novo_usuario.set_password(data['senha'])


    # Cria uma nova instância de EnderecoUsuario
    novo_endereco = EnderecoUsuario(
        cep=data['cep'],
        bairro=data['bairro'],
        rua=data['rua'],
        numero=data['numero'],
        complemento=data.get('complemento'), # Use .get() para campos opcionais
        cidade=data['cidade'],
        estado=data['estado'],
        # O relacionamento com o usuário será estabelecido automaticamente pelo backref
        # ou atribuindo novo_endereco.usuario = novo_usuario ANTES do commit
    )

    # Adiciona o usuário e o endereço à sessão do banco de dados
    db.session.add(novo_usuario)
    # O endereço pode ser adicionado diretamente ou associado ao usuário
    # A associação via backref geralmente adiciona o endereço automaticamente se a relação for one-to-many
    # Se não, você pode adicionar explicitamente: db.session.add(novo_endereco)
    # Ou associar: novo_usuario.enderecos_usuario.append(novo_endereco) # Se lazy='dynamic', use .append()
    novo_endereco.usuario = novo_usuario # Melhor explicitar a associação

    db.session.add(novo_endereco) # Adiciona o endereço à sessão

    try:
        db.session.commit() # Salva as alterações no banco de dados
        return jsonify({'Mensagem': 'Usuário registrado com sucesso'}), 201
    except Exception as e:
        db.session.rollback() # Desfaz as alterações em caso de erro
        print(f"Erro ao registrar usuário: {e}") # Logar o erro no servidor
        return jsonify({'Erro': 'Erro ao registrar usuário'}), 500


# Rota para Login (Nome da função 'login_route' para evitar conflito com login_user)
@app.route('/login', methods=['POST'])
def login_route():
    # Verifica se o usuário já está autenticado
    if current_user.is_authenticated:
        return jsonify({'Mensagem': 'Usuário já logado'}), 200 # Ou redirecionar

    data = request.get_json()

    # Validação básica
    if not all(key in data for key in ['email', 'senha']):
         return jsonify({'Erro': 'Email e senha são obrigatórios'}), 400

    # Busca o usuário pelo email no banco de dados
    user = Usuario.query.filter_by(email=data['email']).first() # Usa o modelo Usuario importado

    # Verifica a senha usando o método check_password do modelo Usuario
    if user and user.check_password(data['senha']):
        # Autentica o usuário com Flask-Login
        login_user(user)
        # Você pode adicionar uma mensagem flash aqui se estiver usando templates
        # flash('Login bem-sucedido!', 'success')
        return jsonify({'Mensagem': 'Logado com sucesso'}), 200
    else:
        # Falha na autenticação
        # flash('Email ou senha inválidos.', 'danger')
        return jsonify({'Erro': 'Email ou senha inválido'}), 401

# Rota para logout
@app.route('/logout')
@login_required # Requer que o usuário esteja logado para fazer logout
def logout():
    logout_user() # Faz logout do usuário atual
    # flash('Você foi desconectado.', 'info') # Mensagem flash
    return jsonify({'Mensagem': 'Sessão encerrada com sucesso'}), 200 # Retorna JSON para API, ou redireciona se for rota web

# --- Execução da Aplicação ---
if __name__ == '__main__':
    # Cria as tabelas do banco de dados se elas não existirem
    # Certifique-se de que o servidor MySQL esteja rodando e o banco de dados 'teste_ecotroca' exista.
    try:
        with app.app_context():
            db.create_all() # Cria as tabelas definidas em backEnd.py
            print("Conectado ao MySQL e verificando/criando tabelas...")
    except Exception as e:
        print(f"Erro fatal ao conectar ao MySQL ou criar tabelas: {e}")

    # Executa o servidor Flask
    # Em produção, mude debug=False e use um servidor WSGI como Gunicorn ou uWSGI
    app.run(debug=True, host='0.0.0.0') # O host='0.0.0.0' permite acesso externo, útil em Docker