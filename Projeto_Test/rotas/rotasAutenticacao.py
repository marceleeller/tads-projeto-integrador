import logging, datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash # Importado para a rota de registro
# Importações adicionais para tokens de refresh e revogação

from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    create_refresh_token, # Importado para criar tokens de refresh
    jwt_refresh_token_required, # Importado para proteger a rota de refresh
    get_jwt # Importado para obter informações do token atual (útil para revogação)
)
import re # Importa regex para validação de email
from camadaModelo import db, Usuario, EnderecoUsuario

# Cria um Blueprint para as rotas de autenticação
# O prefixo '/autenticacao' será adicionado a todas as rotas definidas neste Blueprint
autenticacao = Blueprint('autenticacao', __name__, url_prefix='/autenticacao')

# --- Configuração de Blacklisting (Revogação de Tokens) ---
# Para implementar a revogação de tokens (logout eficaz), você precisa configurar
# um mecanismo de blacklist. Isso geralmente envolve:
# 1. Um local para armazenar os tokens revogados (ex: Redis, banco de dados).
# 2. Configurar o Flask-JWT-Extended na sua aplicação principal (onde você inicializa o JWTManager)
#    para usar um `token_in_blocklist_loader`.
#    Exemplo (na sua app.py ou similar):
#    from flask_jwt_extended import JWTManager
#    jwt = JWTManager(app)
#
#    # Configure a função que verifica se um token está na blacklist
#    # Sua implementação real consultaria o armazenamento da blacklist
#    # @jwt.token_in_blocklist_loader
#    # def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
#    #     jti = jwt_payload["jti"]
#    #     # return jti in SUA_BLACKLIST # Exemplo: consulta a blacklist
#    #     pass # Implementação real aqui

# --- Rotas de Autenticação ---

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

     # Validação de formato de data de nascimento (espera DD-MM-YY)
    try:
        # Corrigido o formato da data para corresponder à string de entrada
        data_nascimento = datetime.datetime.strptime(data['data_nascimento'], '%d-%m-%y').date()
    except ValueError:
        logging.warning(f"Formato de data de nascimento inválido: {data['data_nascimento']}")
        # Mensagem de erro corrigida para refletir o formato esperado
        return jsonify({'erro': 'Formato de data de nascimento inválido. Use DD-MM-YY.'}), 400

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
        # ASSUME que o modelo Usuario tem um método set_password(self, password)
        # Certifique-se de que este método existe e usa generate_password_hash
        novo_usuario.definir_senha(data['senha'])


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
        # ASSUME que o modelo EnderecoUsuario tem um campo 'usuario' que é um relacionamento com Usuario
        novo_endereco.id_usuario = novo_usuario

        # Adiciona o usuário e o endereço à sessão do banco de dados
        db.session.add(novo_usuario)
        db.session.add(novo_endereco)

        # Salva as alterações no banco de dados
        db.session.commit()

        logging.info(f"Usuário registrado com sucesso: {novo_usuario.email}")

        # Retorna uma resposta de sucesso
        # Assumindo que o modelo Usuario tem um atributo 'id' ou 'id_usuario'
        return jsonify({'mensagem': 'Usuário registrado com sucesso', 'id_usuario': novo_usuario.id}), 201 # Created

    except Exception as e:
        # Desfaz as alterações em caso de erro no banco de dados
        db.session.rollback()
        logging.error(f"Erro ao registrar usuário no banco de dados: {e}")
        # Em produção, evite expor detalhes do erro do DB ao usuário final
        return jsonify({'erro': 'Erro ao registrar usuário no banco de dados.'}), 500 # Internal Server Error


@autenticacao.route('/login', methods=['POST'])
def login():
    """
    Endpoint para login de usuário.
    Espera um corpo de requisição JSON com 'email' e 'senha'.
    Valida as credenciais e retorna um JWT de acesso e um JWT de refresh em caso de sucesso.
    """
    data = request.get_json()

    # Valida se os campos obrigatórios estão presentes
    if not data or data.get['email'] not in data or data.get['senha'] not in data:
        logging.warning("Tentativa de login sem email ou senha.")
        return jsonify({'erro': 'Email e senha são obrigatórios.'}), 400 # Bad Request

    email = data.get('email')
    senha = data.get('senha')

    try:
        # Busca o usuário no banco de dados pelo email
        usuario = Usuario.query.filter_by(email=email).first()

        # Verifica se o usuário foi encontrado e se a senha está correta
        if usuario and usuario.verificar_senha(senha):
            # Autenticação bem-sucedida: cria um token JWT de acesso e um token de refresh
            # A identidade do token é o ID do usuário, que será usado em rotas protegidas
            access_token = create_access_token(identity=usuario.id)
            #refresh_token = create_refresh_token(identity=usuario.id) # Cria o token de refresh

            # Retorna os tokens na resposta JSON
            return jsonify({
                'mensagem': 'Autenticação bem-sucedida',
                'access_token': access_token,
            }), 200 # OK
        else:
            # Credenciais inválidas
            logging.warning(f"Tentativa de login falhou para o email: {email}")
            return jsonify({'erro': 'Email ou senha inválidos.'}), 401 # Unauthorized

    except Exception as e:
        # Loga o erro no servidor (não expõe detalhes ao usuário)
        logging.error(f"Erro interno ao autenticar usuário {email}: {e}")
        return jsonify({'erro': 'Ocorreu um erro interno ao tentar autenticar.'}), 500 # Internal Server Error

'''
# --- Nova Rota para Refresh de Token ---
@autenticacao.route('/refresh', methods=['POST'])
@jwt_refresh_token_required() # Exige um token de refresh válido
def refresh():
    """
    Endpoint para obter um novo token de acesso usando um token de refresh válido.
    Requer um token de refresh válido no cabeçalho Authorization (Bearer).
    """
    # get_jwt_identity() funciona para ambos access e refresh tokens se a identidade for a mesma
    current_user_id = get_jwt_identity()

    # Cria um *novo* token de acesso para a mesma identidade
    new_access_token = create_access_token(identity=current_user_id)

    logging.info(f"Novo token de acesso gerado via refresh para o usuário ID: {current_user_id}")

    return jsonify({
        'access_token': new_access_token
    }), 200
'''

# --- Exemplo de Rota para Logout (Requer Configuração de Blacklist) ---
# Esta rota é um exemplo e precisa que a configuração de blacklist esteja ativa
# na sua aplicação principal para funcionar corretamente.
@autenticacao.route('/logout', methods=['POST'])
@jwt_required() # Exige um access token válido para fazer logout
def logout():
    """
    Revoga o token de acesso atual adicionando-o a uma blacklist.
    Requer que a configuração de blacklist esteja ativa na aplicação principal.
    """
    # get_jwt() retorna o payload completo do token atual
    jti = get_jwt().get("jti") # 'jti' é um identificador único para o token

    if jti:
        try:
            # --- Lógica para adicionar o JTI à Blacklist ---
            # Esta parte precisa ser implementada para armazenar o 'jti'
            # em um local persistente (DB, Redis, etc.) que a função
            # `token_in_blocklist_loader` possa consultar.
            # Exemplo conceitual (NÃO USE EM PRODUÇÃO sem persistência):
            # from sua_app import BLOCKLIST # Se você usou um set global (não recomendado para produção)
            # if jti not in BLOCKLIST:
            #     BLOCKLIST.add(jti)
            #     logging.info(f"Token de acesso revogado (JTI): {jti}")
            # else:
            #     logging.warning(f"Tentativa de revogar token já revogado (JTI): {jti}")
            # --- Fim da Lógica de Blacklist ---

            # Como a lógica de blacklist é externa a este blueprint,
            # apenas retornamos sucesso se o JTI foi obtido.
            # A validação real de revogação acontece no `token_in_blocklist_loader`.
            return jsonify({'mensagem': 'Token de acesso processado para revogação.'}), 200 # OK

        except Exception as e:
            logging.error(f"Erro ao processar revogação de token (JTI: {jti}): {e}")
            return jsonify({'erro': 'Ocorreu um erro ao processar a revogação do token.'}), 500 # Internal Server Error
    else:
        logging.warning("Tentativa de logout sem JTI no token.")
        return jsonify({'erro': 'Token inválido ou sem identificador (JTI).'}), 400 # Bad Request

# Exemplo de rota protegida que retorna informações do usuário logado
# Esta rota demonstra como usar @jwt_required() e get_jwt_identity()
@autenticacao.route('/perfil', methods=['GET'])
@jwt_required() # Este decorador exige um JWT de acesso válido na requisição
def perfil():
    """
    Rota de exemplo protegida que retorna informações básicas do usuário logado.
    Requer um JWT de acesso válido no cabeçalho Authorization.
    """
    # get_jwt_identity() extrai a identidade do usuário (o ID que passamos em create_access_token)
    current_user_id = get_jwt_identity()

    try:
        # Busca o objeto Usuario no banco de dados usando o ID obtido do token
        # Assumindo que o modelo Usuario tem um atributo 'id'
        usuario = Usuario.query.get(current_user_id)
        if usuario is None:
             # Isso não deveria acontecer se o token for válido e o DB estiver consistente
             logging.error(f"Usuário com ID {current_user_id} não encontrado, apesar do token ser válido.")
             return jsonify({'erro': 'Usuário não encontrado.'}), 404 # Not Found

        # Retorna as informações do usuário logado em formato JSON
        # Assumindo que o modelo Usuario tem atributos 'id', 'nome_usuario', 'email'
        return jsonify({
            'mensagem': 'Informações do perfil (via JWT)',
            'id': usuario.id,
            'nome_usuario': usuario.nome_usuario,
            'email': usuario.email
        }), 200 # OK

    except Exception as e:
        logging.error(f"Erro ao obter perfil do usuário {current_user_id}: {e}")
        return jsonify({'erro': 'Ocorreu um erro interno ao obter as informações do perfil.'}), 500 # Internal Server Error
