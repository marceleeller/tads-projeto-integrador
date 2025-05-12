# Importa as bibliotecas e módulos necessários
import os # Importa o módulo os para acessar variáveis de ambiente
import pymysql
import uuid
from flask import Flask, request,secure_filename, jsonify,render_template_string,send_from_directory,render_template, redirect, url_for, flash, get_flashed_messages, g
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash # Necessário para métodos de senha
import logging # Importa o módulo de logging
import re # Importa regex para validação de email
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # Importa componentes do Flask-Login
from camadaModelo import Usuario,EnderecoUsuario,db,TipoDeInterese,Produto,Imagem
# Configura o logging básico
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

# Configuração para upload de arquivos
# Cria um diretório 'uploads' se não existir
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limite de 16MB para uploads

logging.info(f"SECRET_KEY configurada.")
logging.info(f"SQLALCHEMY_DATABASE_URI configurada.")
logging.info(f"UPLOAD_FOLDER configurado para: {UPLOAD_FOLDER}")


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

# Inicializa o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# Define a view para onde o usuário será redirecionado se tentar acessar uma rota protegida sem estar logado.
# Neste caso de API, vamos usar um unauthorized_handler para retornar JSON.
# login_manager.login_view = 'login' # Descomente e ajuste se usar templates HTML
login_manager.session_protection = "strong" # Proteção de sessão recomendada

logging.info("Flask-Login inicializado.")

# --- Funções de Callback do Flask-Login ---

@login_manager.user_loader
def load_user(user_id):
    """
    Callback usado pelo Flask-Login para carregar um usuário a partir do seu ID.
    Este ID é armazenado na sessão.
    Retorna o objeto Usuario correspondente ao ID, ou None se o usuário não for encontrado.
    """
    if Usuario and db: # Verifica se o modelo Usuario e o objeto db foram importados
        try:
            # O ID armazenado na sessão pelo Flask-Login é uma string, então convertemos para int
            user = Usuario.query.get(int(user_id))
            if user:
                logging.debug(f"Usuário carregado: {user.email}")
            else:
                logging.debug(f"Usuário com ID {user_id} não encontrado.")
            return user
        except ValueError:
            logging.error(f"ID de usuário inválido na sessão: {user_id}")
            return None
        except Exception as e:
            logging.error(f"Erro ao carregar usuário com ID {user_id}: {e}")
            return None
    logging.warning("load_user chamado, mas Usuario ou db não estão disponíveis.")
    return None

@login_manager.unauthorized_handler
def unauthorized():
    """
    Handler chamado pelo Flask-Login quando um usuário não autenticado tenta acessar
    uma rota protegida por @login_required.
    Neste caso de API, retornamos um JSON de erro 401.
    """
    logging.warning("Acesso não autorizado a rota protegida.")
    return jsonify({'erro': 'Autenticação necessária para acessar este recurso.'}), 401


# --- Definição das Rotas da Aplicação ---

# Rota de exemplo para a página inicial (pode ser um formulário de cadastro ou login)
@app.route('/')
def index():
    # Renderiza um template HTML simples ou retorna um JSON informativo
    # Mantido para compatibilidade com o código original que renderiza um template.
    # Se for uma API pura, esta rota pode ser removida ou modificada.
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Página Inicial</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <h1>Bem-vindo!</h1>
        <p>Esta é a página inicial. Use os endpoints da API para interagir.</p>
        <p>Endpoints disponíveis:</p>
        <ul>
            <li>POST /registro - Para registrar novos usuários</li>
            <li>POST /login - Para autenticar usuários</li>
            <li>POST /logout - Para deslogar usuários (requer autenticação)</li>
            <li>POST /create_product - Para cadastrar produtos (requer autenticação)</li>
            <li>GET /protected - Exemplo de rota protegida (requer autenticação)</li>
        </ul>
    </body>
    </html>
    """)


# Rota para registro de Usuario (mantida, não protegida por login, pois é para novos usuários)
@app.route('/registro', methods=['POST'])
def register():
    """
    Endpoint para registrar um novo usuário e seu endereço.
    Espera um corpo de requisição JSON com os dados do usuário e endereço.
    """
    # Verifica se os modelos necessários foram importados
    if not Usuario or not EnderecoUsuario or not db:
        logging.error("Erro interno: Modelos ou objeto DB não carregados para registro.")
        return jsonify({'erro': 'Erro interno do servidor: Recursos de registro não disponíveis.'}), 500 # Internal Server Error

    # Obtém os dados JSON do corpo da requisição
    data = request.get_json()

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

    # Validação de formato de data de nascimento (espera-MM-DD)
    try:
        data_nascimento = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()
    except ValueError:
        logging.warning(f"Formato de data de nascimento inválido: {data['data_nascimento']}")
        return jsonify({'erro': 'Formato de data de nascimento inválido. Use-MM-DD.'}), 400

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

# Rota para autenticação de usuário (login)
@app.route('/login', methods=['POST'])
def login():
    """
    Endpoint para autenticar um usuário.
    Espera um corpo de requisição JSON com 'email' e 'senha'.
    Se a autenticação for bem-sucedida, loga o usuário usando Flask-Login.
    Retorna uma resposta JSON indicando sucesso ou falha.
    """
    # Se o usuário já estiver autenticado, podemos retornar uma mensagem
    if current_user.is_authenticated:
        logging.info(f"Tentativa de login de usuário já autenticado: {current_user.email}")
        return jsonify({'mensagem': 'Usuário já autenticado.'}), 200

    # Obtém os dados JSON da requisição
    data = request.get_json()

    # Valida se os dados JSON foram recebidos e se os campos obrigatórios estão presentes
    if not data or 'email' not in data or 'senha' not in data:
        logging.warning("Tentativa de login sem corpo JSON ou campos faltando.")
        return jsonify({'erro': 'Email e senha são obrigatórios'}), 400 # Bad Request

    email = data['email']
    senha = data['senha']

    # Verifica se o modelo Usuario foi importado antes de tentar usá-lo
    if not Usuario or not db:
        logging.error("Erro interno: Modelo de usuário ou objeto DB não carregado durante o login.")
        return jsonify({'erro': 'Erro interno do servidor: Recurso de usuário não disponível.'}), 500 # Internal Server Error

    try:
        # Busca o usuário no banco de dados pelo email. Assume que o email é único.
        usuario = Usuario.query.filter_by(email=email).first()

        # Verifica se o usuário foi encontrado E se a senha fornecida corresponde ao hash armazenado
        if usuario and check_password_hash(usuario.password_hash, senha):
            # Autenticação bem-sucedida
            # Usa login_user() do Flask-Login para logar o usuário na sessão
            login_user(usuario) # Opcional: remember=True para funcionalidade "Lembrar-me"

            logging.info(f"Usuário autenticado com sucesso: {email}")

            # Retorna uma resposta 200 (OK) com dados básicos do usuário
            return jsonify({
                'mensagem': 'Autenticação bem-sucedida',
                'id_usuario': usuario.id_usuario,
                'nome_usuario': usuario.nome_usuario,
                'email': usuario.email
                # Considere adicionar um token JWT aqui para APIs RESTful sem estado
            }), 200
        else:
            # Usuário não encontrado ou senha incorreta
            logging.warning(f"Tentativa de login falhou para o email: {email}")
            return jsonify({'erro': 'Email ou senha inválidos.'}), 401 # Unauthorized

    except Exception as e:
        # Captura quaisquer outros erros que possam ocorrer durante a consulta ao DB
        logging.error(f"Erro inesperado durante a autenticação para o email {email}: {e}")
        return jsonify({'erro': 'Ocorreu um erro interno ao tentar autenticar.'}), 500

# Rota para deslogar o usuário
@app.route('/logout', methods=['POST'])
@login_required # Esta rota só pode ser acessada por usuários autenticados
def logout():
    """
    Endpoint para deslogar o usuário autenticado.
    Usa logout_user() do Flask-Login.
    """
    logging.info(f"Usuário deslogado: {current_user.email}")
    logout_user()
    return jsonify({'mensagem': 'Usuário deslogado com sucesso.'}), 200

# Rota para cadastro de produto (AGORA PROTEGIDA POR LOGIN)
@app.route('/create_product', methods=['POST'])
@login_required # Apenas usuários logados podem acessar esta rota
def cadastro_produto():
    """
    Endpoint para cadastrar um novo produto com informações e imagens.
    Recebe dados do formulário e arquivos de imagem.
    """
    # Verifica se os modelos necessários foram importados
    if not Produto or not TipoDeInterese or not Imagem or not db:
        logging.error("Erro interno: Modelos (Produto, Imagem, Enum) ou objeto DB não carregados para cadastro de produto.")
        return jsonify({'erro': 'Erro interno do servidor: Recursos de produto não disponíveis.'}), 500 # Internal Server Error

    # Obtém dados do formulário
    nome = request.form.get('nome')
    descricao = request.form.get('descricao')
    interesse_str = request.form.get('interesse') # Recebe como string

    # Validação básica dos campos de texto
    if not nome or not descricao or not interesse_str:
        logging.warning("Campos obrigatórios faltando no cadastro de produto.")
        return jsonify({"erro": "Nome, descrição e interesse são obrigatórios"}), 400

    # Valida o valor do interesse
    try:
        interesse = TipoDeInterese[interesse_str.upper()] # Converte a string para o Enum
    except KeyError:
        logging.warning(f"Valor de interesse inválido no cadastro de produto: {interesse_str}")
        return jsonify({"erro": "Valor de interesse inválido. Use 'troca' ou 'doacao'."}), 400

    # Obtém os arquivos de imagem
    imagens_arquivos = request.files.getlist('imagens') # 'imagens' é o nome do input de arquivo no formulário

    if not imagens_arquivos or imagens_arquivos[0].filename == '':
        logging.warning("Nenhuma imagem fornecida no cadastro de produto.")
        return jsonify({"erro": "Pelo menos uma imagem é obrigatória"}), 400

    # --- Criação e Persistência do Produto e Imagens ---
    try:
        # Cria uma nova instância do modelo Produto
        new_product = Produto(
            nome_produto=nome,
            descricao=descricao,
            interesse=interesse, # Armazena o valor do Enum
            id_usuario=current_user.id_usuario # Associa o produto ao usuário logado
        )

        # Lista para armazenar as instâncias de Imagem
        imagens_instancias = []

        # Processa e salva as imagens
        for imagem_arquivo in imagens_arquivos:
            if imagem_arquivo:
                # Gera um nome de arquivo seguro
                filename = secure_filename(imagem_arquivo.filename)
                # Cria um caminho único para o arquivo para evitar colisões
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                try:
                    # Salva o arquivo no sistema de arquivos
                    imagem_arquivo.save(filepath)

                    # Cria uma instância de Imagem
                    new_image = Imagem(
                        url_imagem=unique_filename, # Armazena apenas o nome único do arquivo
                        # descricao_imagem pode ser adicionado se o formulário fornecer
                        produto=new_product # Associa a imagem ao produto (assumindo relacionamento configurado)
                    )
                    imagens_instancias.append(new_image)

                except Exception as e:
                    logging.error(f"Erro ao salvar imagem {filename}: {e}")
                    # Em caso de erro ao salvar uma imagem, você pode querer deletar arquivos já salvos para esta requisição
                    # e/ou reverter a transação do DB. Para simplificar, retornamos um erro.
                    return jsonify({"erro": f"Erro ao salvar imagem {filename}"}), 500

        # Adiciona o novo produto e suas imagens à sessão do banco de dados
        db.session.add(new_product)
        # As imagens serão adicionadas automaticamente se o relacionamento com cascade estiver configurado no modelo Produto
        # Caso contrário, adicione explicitamente: db.session.add_all(imagens_instancias)
        db.session.add_all(imagens_instancias) # Adiciona explicitamente para garantir

        # Salva as alterações no banco de dados
        db.session.commit()

        logging.info(f"Produto '{new_product.nome_produto}' cadastrado com sucesso pelo usuário {current_user.email}.")

        # Prepara a resposta de sucesso
        response_product = {
            'id_produto': new_product.id_produto, # Use o nome correto do atributo PK
            'nome_produto': new_product.nome_produto,
            'descricao': new_product.descricao,
            'interesse': new_product.interesse.value, # Retorna o valor da string do Enum
            'id_usuario': new_product.id_usuario,
            # 'data_cadastro': new_product.data_cadastro.isoformat(), # Descomente se tiver este campo no modelo Produto
            'imagens': [img.url_imagem for img in new_product.imagens] # Lista dos nomes dos arquivos
        }

        return jsonify({"mensagem": "Produto cadastrado com sucesso", "produto": response_product}), 201 # Created

    except Exception as e:
        # Desfaz as alterações em caso de erro no banco de dados
        db.session.rollback()
        logging.error(f"Erro ao registrar produto no banco de dados: {e}")
        # Em produção, evite expor detalhes do erro do DB ao usuário final
        return jsonify({'erro': 'Erro ao registrar produto no banco de dados.'}), 500 # Internal Server Error


# Rota para servir arquivos estáticos (imagens) - Útil para visualização
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Rota para servir arquivos da pasta de uploads.
    """
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        logging.warning(f"Arquivo não encontrado na pasta de uploads: {filename}")
        return jsonify({'erro': 'Arquivo não encontrado.'}), 404 # Not Found
    except Exception as e:
        logging.error(f"Erro ao servir arquivo {filename}: {e}")
        return jsonify({'erro': 'Erro interno ao servir arquivo.'}), 500


# Rota de exemplo para exibir o formulário de upload (apenas para demonstração)
# Mantido para compatibilidade, mas em uma API pura, você não renderizaria HTML.
@app.route('/upload_form') # Alterado o nome da rota para evitar conflito com '/'
def upload_form():
    """
    Renderiza um formulário HTML simples para testar o upload de produtos.
    """
    html_form = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cadastrar Produto</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <style>
            body {
                font-family: 'Inter', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background-color: #f0f4f8;
            }
            .container {
                background-color: #ffffff;
                padding: 2rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 500px;
            }
            input[type="file"]::file-selector-button {
                margin-right: 20px;
                border: none;
                background: #0b63e5;
                padding: 10px 20px;
                border-radius: 10px;
                color: #fff;
                cursor: pointer;
                transition: background .2s ease-in-out;
            }

            input[type="file"]::file-selector-button:hover {
                background: #084cd1;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="text-2xl font-bold mb-6 text-center">Cadastrar Novo Produto</h2>
            <form action="/create_product" method="post" enctype="multipart/form-data">
                <div class="mb-4">
                    <label for="nome" class="block text-gray-700 text-sm font-bold mb-2">Nome do Produto:</label>
                    <input type="text" id="nome" name="nome" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" required>
                </div>
                <div class="mb-4">
                    <label for="descricao" class="block text-gray-700 text-sm font-bold mb-2">Descrição:</label>
                    <textarea id="descricao" name="descricao" rows="4" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" required></textarea>
                </div>
                <div class="mb-4">
                    <label for="interesse" class="block text-gray-700 text-sm font-bold mb-2">Interesse:</label>
                    <select id="interesse" name="interesse" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" required>
                        <option value="troca">Troca</option>
                        <option value="doacao">Doação</option>
                    </select>
                </div>
                <div class="mb-4">
                    <label for="imagens" class="block text-gray-700 text-sm font-bold mb-2">Imagens do Produto:</label>
                    <input type="file" id="imagens" name="imagens" accept="image/*" multiple class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" required>
                    <p class="text-xs text-gray-600 mt-1">Selecione uma ou mais imagens.</p>
                </div>
                <div class="flex items-center justify-between">
                    <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                        Cadastrar
                    </button>
                </div>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_form)

# Rota de exemplo protegida
@app.route('/protected', methods=['GET'])
@login_required # Este decorador garante que apenas usuários autenticados podem acessar esta rota
def protected_route():
    """
    Endpoint de exemplo que só pode ser acessado por usuários autenticados.
    Demonstra o uso do decorador @login_required e acesso a current_user.
    """
    # current_user é fornecido pelo Flask-Login e representa o usuário logado
    logging.info(f"Acesso permitido a rota protegida por usuário: {current_user.email}")
    return jsonify({
        'mensagem': f'Olá, {current_user.nome_usuario}! Você acessou uma rota protegida.',
        'id_usuario': current_user.id_usuario
    }), 200


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
