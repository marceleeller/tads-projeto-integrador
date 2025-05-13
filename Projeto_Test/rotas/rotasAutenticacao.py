import logging,datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash,check_password_hash # Importado para a rota de registro
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import re # Importa regex para validação de email
from camadaModelo import db, Usuario,EnderecoUsuario

# Cria um Blueprint para as rotas de autenticação
# O prefixo '/autenticacao' será adicionado a todas as rotas definidas neste Blueprint
autenticacao = Blueprint('autenticacao', __name__, url_prefix='/autenticacao')

# --- Rotas de Autenticação ---

@autenticacao.route('/login', methods=['POST'])
def login():
    """
    Endpoint para login de usuário.
    Espera um corpo de requisição JSON com 'email' e 'senha'.
    Valida as credenciais e retorna um JWT de acesso em caso de sucesso.
    """
    data = request.get_json()

    # Valida se os campos obrigatórios estão presentes
    if not data or 'email' not in data or 'senha' not in data:
        return jsonify({'erro': 'Email e senha são obrigatórios.'}), 400 # Bad Request

    email = data.get('email')
    senha = data.get('senha')

    try:
        # Busca o usuário no banco de dados pelo email
        usuario = Usuario.query.filter_by(email=email).first()

        # Verifica se o usuário foi encontrado e se a senha está correta
        if usuario and usuario.check_password(senha):
            # Autenticação bem-sucedida: cria um token JWT de acesso
            # A identidade do token é o ID do usuário, que será usado em rotas protegidas
            access_token = create_access_token(identity=usuario.id)

            # Retorna o token de acesso na resposta JSON
            return jsonify({
                'mensagem': 'Autenticação bem-sucedida',
                'access_token': access_token
            }), 200 # OK
        else:
            # Credenciais inválidas
            return jsonify({'erro': 'Email ou senha inválidos.'}), 401 # Unauthorized

    except Exception as e:
        # Loga o erro no servidor (não expõe detalhes ao usuário)
        print(f"Erro ao autenticar usuário: {e}")
        return jsonify({'erro': 'Ocorreu um erro interno ao tentar autenticar.'}), 500 # Internal Server Error

@autenticacao.route('/registrar', methods=['POST'])
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

# Exemplo de rota protegida que retorna informações do usuário logado
# Esta rota demonstra como usar @jwt_required() e get_jwt_identity()
@autenticacao.route('/perfil', methods=['GET'])
@jwt_required() # Este decorador exige um JWT válido na requisição
def perfil():
    """
    Rota de exemplo protegida que retorna informações básicas do usuário logado.
    Requer um JWT de acesso válido no cabeçalho Authorization.
    """
    # get_jwt_identity() extrai a identidade do usuário (o ID que passamos em create_access_token)
    current_user_id = get_jwt_identity()

    try:
        # Busca o objeto Usuario no banco de dados usando o ID obtido do token
        usuario = Usuario.query.get(current_user_id)
        if usuario is None:
             # Isso não deveria acontecer se o token for válido e o DB estiver consistente
             return jsonify({'erro': 'Usuário não encontrado.'}), 404 # Not Found

        # Retorna as informações do usuário logado em formato JSON
        return jsonify({
            'mensagem': 'Informações do perfil (via JWT)',
            'id': usuario.id,
            'nome_usuario': usuario.nome_usuario,
            'email': usuario.email
        }), 200 # OK

    except Exception as e:
        print(f"Erro ao obter perfil do usuário {current_user_id}: {e}")
        return jsonify({'erro': 'Ocorreu um erro interno ao obter as informações do perfil.'}), 500 # Internal Server Error
