# Importa as bibliotecas e módulos necessários
import os # Importa o módulo os para acessar variáveis de ambiente
import pymysql
from flask import Flask, request, jsonify,render_template, redirect, url_for, flash, get_flashed_messages, g
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash # Necessário para métodos de senha
import logging # Importa o módulo de logging
import re # Importa regex para validação de email
from camadaModelo import db, Usuario, EnderecoUsuario, StatusProduto, StatusSolicitacao

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Instala o pymysql como driver padrão para MySQL
pymysql.install_as_MySQLdb()
logging.info("pymysql instalado como driver MySQL.")

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
    try:
        db.init_app(app)
        logging.info("Flask-SQLAlchemy inicializado com o app.")
    except Exception as e:
        logging.error(f"Erro ao inicializar Flask-SQLAlchemy: {e}")
        db = None # Garante que db seja None se a inicialização falhar
else:
     logging.warning("Aviso: Flask-SQLAlchemy não foi inicializado devido a erro na importação do 'db'.")


# --- Definição das Rotas da Aplicação ---

@app.route('/')
def index():
    # Renderiza o template que contém o formulário de cadastro
    # Em uma API REST pura, esta rota pode não existir ou retornar um JSON informativo.
    # Mantido para compatibilidade com o código original que renderiza um template.
    return render_template("cadastro.html")

# Rota para registro de Usuario
@app.route('/Registro', methods=['POST'])
def register():
    """
    Endpoint para registrar um novo usuário e seu endereço.
    Espera um corpo de requisição JSON com os dados do usuário e endereço.
    """

     # Obtém os dados JSON do corpo da requisição
    data = request.get_json()

    # Verifica se os modelos necessários foram importados
    if not Usuario or not EnderecoUsuario or not db:
        logging.error("Erro interno: Modelos ou objeto DB não carregados para registro.")
        return jsonify({'erro': 'Erro interno do servidor: Recursos de registro não disponíveis.'}), 500 # Internal Server Error

   # --- Validação dos Dados de Entrada ---
    if not data:
        logging.warning("Tentativa de registro sem corpo JSON.")
        return jsonify({'erro': 'Corpo da requisição deve ser JSON.'}), 400 # Bad Request

    # Lista de campos obrigatórios
    required_fields = ['nome', 'cpf', 'telefone', 'email', 'senha', 'confirme_a_sua_senha',
                       'cep', 'bairro', 'rua', 'numero', 'cidade', 'estado', 'data_nascimento']

    # Verifica se todos os campos obrigatórios estão presentes e não são None
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
         logging.warning(f"Campos obrigatórios faltando no registro: {missing_fields}")
         return jsonify({'erro': f'Campos obrigatórios faltando: {", ".join(missing_fields)}'}), 400

    # Validação de senhas
    if data['senha'] != data['confirme_a_sua_senha']:
        logging.warning("Senhas não coincidem durante o registro.")
        return jsonify({'erro': 'As senhas não coincidem.'}), 400

    # Validação básica de formato de email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
         logging.warning(f"Formato de email inválido: {data['email']}")
         return jsonify({'erro': 'Formato de email inválido.'}), 400

    # Validação de formato de data de nascimento (espera YYYY-MM-DD)
    try:
        data_nascimento = datetime.strptime(data['data_nascimento'], '%d-%M-%y').date()
    except ValueError:
        logging.warning(f"Formato de data de nascimento inválido: {data['data_nascimento']}")
        return jsonify({'erro': 'Formato de data de nascimento inválido. Use YYYY-MM-DD.'}), 400

    # --- Verificação de Unicidade (Email e CPF) ---
    try:
        # Verifica se o email já existe
        if Usuario.query.filter_by(email=data['email']).first():
            logging.warning(f"Tentativa de registro com email já existente: {data['email']}")
            return jsonify({'erro': 'Email já foi registrado.'}), 409 # Conflict

        # Verifica se o CPF já existe (se CPF for obrigatório e único)
        # Assumindo que CPF é obrigatório e único com base no seu código original
        if Usuario.query.filter_by(cpf=data['cpf']).first():
             logging.warning(f"Tentativa de registro com CPF já existente: {data['cpf']}")
             return jsonify({'erro': 'CPF já registrado.'}), 409 # Conflict

    except Exception as e:
        logging.error(f"Erro ao verificar unicidade de email/CPF: {e}")
        # Em produção, evite expor detalhes do erro do DB ao usuário final
        return jsonify({'erro': 'Ocorreu um erro ao verificar dados existentes.'}), 500


    # --- Criação e Persistência dos Objetos ---
    try:
        # Cria uma nova instância de Usuario
        novo_usuario = Usuario(
            nome_usuario=data['nome'],
            cpf=data['cpf'],
            telefone=data['telefone'],
            email=data['email'],
            data_nascimento=data_nascimento # Usa o objeto date validado
        )
        # Define a senha usando o método do modelo para gerar o hash
        # ASSUME que o modelo Usuario tem um método set_password
        novo_usuario.set_password(data['senha'])


        # Cria uma nova instância de EnderecoUsuario
        novo_endereco = EnderecoUsuario(
            cep=data['cep'],
            bairro=data['bairro'],
            rua=data['rua'],
            numero=data['numero'],
            complemento=data.get('complemento'), # Usa .get() para campos opcionais
            cidade=data['cidade'],
            estado=data['estado'],
            # O relacionamento com o usuário será estabelecido abaixo
        )

        # Associa o endereço ao usuário
        novo_endereco.usuario = novo_usuario

        # Adiciona o usuário e o endereço à sessão do banco de dados
        db.session.add(novo_usuario)
        db.session.add(novo_endereco)

        # Salva as alterações no banco de dados
        db.session.commit()

        logging.info(f"Usuário registrado com sucesso: {novo_usuario.email}")

        # Retorna uma resposta de sucesso
        return jsonify({'mensagem': 'Usuário registrado com sucesso', 'id_usuario': novo_usuario.id_usuario}), 201 # Created

    except Exception as e:
        # Desfaz as alterações em caso de erro no banco de dados
        db.session.rollback()
        logging.error(f"Erro ao registrar usuário no banco de dados: {e}")
        # Em produção, evite expor detalhes do erro do DB ao usuário final
        return jsonify({'erro': 'Erro ao registrar usuário no banco de dados.'}), 500 # Internal Server Error


# --- Execução da Aplicação ---
# Este bloco de execução é útil para rodar este script diretamente para testes.
# Em uma aplicação maior, a execução principal geralmente fica em um arquivo 'app.py'
# que importa e registra esta API.
if __name__ == '__main__':
    if db: # Verifica se 'db' foi inicializado
        with app.app_context():
            try:
                # Cria as tabelas do banco de dados se elas não existirem.
                # Certifique-se de que o servidor MySQL esteja rodando e o banco de dados exista.
                db.create_all()
                logging.info("Banco de dados conectado e tabelas verificadas/criadas.")
            except Exception as e:
                logging.error(f"Erro fatal ao conectar ou criar tabelas do MySQL: {e}")
    else:
        logging.warning("db.create_all() não foi executado porque 'db' não foi inicializado.")

    logging.info("Iniciando o servidor Flask...")
    # Use debug=True apenas durante o desenvolvimento. Mude para False em produção.
    # host='0.0.0.0' permite que o servidor seja acessível externamente (útil em ambientes como Docker).
    # port=5000 define a porta em que o servidor irá rodar.
    app.run(debug=True, host='0.0.0.0', port=5000) # Porta padrão 5000, ajuste se necessário
