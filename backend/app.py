import os
from datetime import timedelta, datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from sqlalchemy.orm import joinedload, selectinload 
from sqlalchemy import or_, and_

from models import (
    db, Usuario, Produto, Imagem, Categoria, Mensagem,
    Solicitacao, Transacao, EnderecoUsuario,
    StatusSolicitacao, TipoDeInterese, tabela_produto_categoria
)

# Configuracão (transferir segredos pra um .env depois)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)


db.init_app(app)
jwt = JWTManager(app)

def parse_date(date_string):
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None

def get_current_user_id_from_token():
    current_user_id_str = get_jwt_identity()
    try:
        return int(current_user_id_str)
    except ValueError:
        raise ValueError("ID de usuário inválido no token")


# POST - Cadastro de usuário
@app.route('/usuario/cadastro', methods=['POST'])
def cadastro_usuario():
    data = request.get_json()
    if not data: 
        return jsonify({'msg': 'Payload da requisição não pode ser vazio'}), 400
    if not all(k in data for k in ('nome_usuario', 'email', 'senha', 'telefone', 'data_nascimento')):
        return jsonify({'msg': 'Campos obrigatórios faltando: nome_usuario, email, senha, telefone, data_nascimento'}), 400

    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({'msg': 'Email já cadastrado'}), 409
    
    data_nasc = parse_date(data.get('data_nascimento'))
    if not data_nasc:
        return jsonify({'msg': 'Formato de data_nascimento inválido. Use YYYY-MM-DD.'}), 400

    novo_usuario = Usuario(
        nome_usuario=data['nome_usuario'],
        email=data['email'],
        telefone=data['telefone'],
        cpf=data.get('cpf'),
        data_nascimento=data_nasc
    )
    novo_usuario.set_password(data['senha'])
    
    try:
        db.session.add(novo_usuario)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao salvar usuário: {e}") 
        return jsonify({'msg': 'Erro ao salvar usuário no banco de dados.'}), 500
    
    return jsonify({'msg': 'Usuário cadastrado com sucesso!', 'id_usuario': novo_usuario.id_usuario}), 201

# POST - Login de usuário
@app.route('/usuario/login', methods=['POST'])
def login_usuario():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('senha'):
        return jsonify({'msg': 'Email e senha são obrigatórios'}), 400

    usuario = Usuario.query.filter_by(email=data['email']).first()

    if usuario and usuario.check_password(data['senha']):
        access_token = create_access_token(identity=str(usuario.id_usuario))
        return jsonify(
            access_token=access_token,
            id_usuario=usuario.id_usuario,
            nome_usuario=usuario.nome_usuario
        ), 200
    return jsonify({'msg': 'Email ou senha inválidos'}), 401


# GET - Obter todos produtos (ativos)
@app.route('/produtos', methods=['GET'])
@jwt_required()
def obter_todos_produtos_ativos():
    # Subconsulta para IDs de produtos desejados em solicitações PENDENTES ou APROVADAS
    sq_desejados = db.select(Solicitacao.id_produto_desejado.distinct().label("produto_id"))\
        .where(Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA]))\
        .where(Solicitacao.id_produto_desejado.isnot(None))

    # Subconsulta para IDs de produtos ofertados em solicitações PENDENTES ou APROVADAS
    sq_ofertados = db.select(Solicitacao.id_produto_ofertado.distinct().label("produto_id"))\
        .where(Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA]))\
        .where(Solicitacao.id_produto_ofertado.isnot(None))
        
    # Executa as subconsultas e obtém as listas de IDs
    ids_desejados_result = db.session.execute(sq_desejados).scalars().all()
    ids_ofertados_result = db.session.execute(sq_ofertados).scalars().all()

    # Combina os IDs de forma única (usando set para remover duplicatas)
    todos_ids_produtos_em_negociacao = list(set(ids_desejados_result + ids_ofertados_result))

    if not todos_ids_produtos_em_negociacao:
        # Se não há produtos em negociação, retorna todos os produtos
        produtos_ativos = Produto.query.all()
    else:
        # Filtra os produtos cujo ID NÃO ESTÁ na lista de produtos em negociação
        produtos_ativos = Produto.query.filter(
            Produto.id_produto.notin_(todos_ids_produtos_em_negociacao)
        ).all()
    
    return jsonify([produto.to_dict(include_owner=True) for produto in produtos_ativos]), 200

# GET - Obter todos produtos vinculados ao ID do usuário (logado)
@app.route('/produtos/usuario', methods=['GET'])
@jwt_required()
def obter_produtos_usuario():
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400 
    
    produtos_cadastrados = Produto.query.filter_by(id_usuario=current_user_id).all()
    solicitacoes_feitas = Solicitacao.query.filter_by(id_usuario_solicitante=current_user_id).all()
    
    produtos_desejados_ids = {s.id_produto_desejado for s in solicitacoes_feitas}
    produtos_ofertados_ids = {s.id_produto_ofertado for s in solicitacoes_feitas if s.id_produto_ofertado}

    todos_ids_relevantes = {p.id_produto for p in produtos_cadastrados}
    todos_ids_relevantes.update(produtos_desejados_ids)
    todos_ids_relevantes.update(produtos_ofertados_ids)

    if not todos_ids_relevantes:
        return jsonify([]), 200

    produtos_relevantes = Produto.query.filter(Produto.id_produto.in_(list(todos_ids_relevantes))).all()
        
    return jsonify([p.to_dict(include_owner=True) for p in produtos_relevantes]), 200


# GET - Obter produto pelo ID
@app.route('/produto/<int:id_produto>', methods=['GET'])
@jwt_required()
def obter_produto(id_produto):
    stmt = db.select(Produto).options(
        joinedload(Produto.proprietario),
        selectinload(Produto.imagens),
        selectinload(Produto.categorias)
    ).where(Produto.id_produto == id_produto)
    produto = db.session.execute(stmt).scalar_one_or_none()
    
    if not produto:
        return jsonify({'msg': 'Produto não encontrado'}), 404
    return jsonify(produto.to_dict(include_owner=True, include_categorias=True, include_imagens=True)), 200

# POST - Criar produto
@app.route('/produto', methods=['POST'])
@jwt_required()
def criar_produto():
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400
        
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'Payload da requisição não pode ser vazio'}), 400

    if not all(k in data for k in ('nome_produto', 'descricao', 'interesse')):
        return jsonify({'msg': 'Campos nome_produto, descricao, interesse são obrigatórios'}), 400

    try:
        tipo_interesse = TipoDeInterese[data['interesse'].upper()]
    except KeyError:
        return jsonify({'msg': f"Valor inválido para 'interesse'. Use {', '.join([t.value for t in TipoDeInterese])}"}), 400

    novo_produto = Produto(
        nome_produto=data['nome_produto'],
        descricao=data['descricao'],
        id_usuario=current_user_id,
        interesse=tipo_interesse,
    )
    db.session.add(novo_produto)
    
    if 'categorias_ids' in data and isinstance(data['categorias_ids'], list):
        for cat_id in data['categorias_ids']:
            categoria = Categoria.query.get(cat_id)
            if categoria:
                novo_produto.categorias.append(categoria)
    
    if 'imagens' in data and isinstance(data['imagens'], list):
        for img_data in data['imagens']:
            if isinstance(img_data, dict) and 'url_imagem' in img_data:
                nova_imagem = Imagem(
                    url_imagem=img_data['url_imagem'],
                    descricao_imagem=img_data.get('descricao_imagem'),
                    produto=novo_produto 
                )
                db.session.add(nova_imagem)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao criar produto: {e}")
        return jsonify({'msg': 'Erro ao salvar produto no banco de dados.'}), 500
        
    return jsonify(novo_produto.to_dict(include_owner=True)), 201


# PUT - Alterar produto
@app.route('/produto/<int:id_produto>', methods=['PUT'])
@jwt_required()
def alterar_produto(id_produto):
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400
        
    produto = Produto.query.get(id_produto)

    if not produto:
        return jsonify({'msg': 'Produto não encontrado'}), 404
    if produto.id_usuario != current_user_id:
        return jsonify({'msg': 'Acesso não autorizado para alterar este produto'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'msg': 'Payload da requisição não pode ser vazio'}), 400
        
    if 'nome_produto' in data:
        produto.nome_produto = data['nome_produto']
    if 'descricao' in data:
        produto.descricao = data['descricao']
    if 'interesse' in data:
        try:
            produto.interesse = TipoDeInterese[data['interesse'].upper()]
        except KeyError:
            return jsonify({'msg': f"Valor inválido para 'interesse'. Use {', '.join([t.value for t in TipoDeInterese])}"}), 400
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao alterar produto {id_produto}: {e}")
        return jsonify({'msg': 'Erro ao atualizar produto no banco de dados.'}), 500
        
    return jsonify(produto.to_dict(include_owner=True)), 200

# DELETE - Deletar produto
@app.route('/produto/<int:id_produto>', methods=['DELETE'])
@jwt_required()
def deletar_produto(id_produto):
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400
        
    produto = Produto.query.get(id_produto)

    if not produto:
        return jsonify({'msg': 'Produto não encontrado'}), 404
    if produto.id_usuario != current_user_id:
        return jsonify({'msg': 'Acesso não autorizado para deletar este produto'}), 403

    solicitacoes_ativas = Solicitacao.query.filter(
        (Solicitacao.id_produto_desejado == id_produto) | (Solicitacao.id_produto_ofertado == id_produto),
        Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA])
    ).first()

    if solicitacoes_ativas:
        return jsonify({'msg': 'Produto não pode ser deletado pois está envolvido em negociações ativas.'}), 409
    try:
        db.session.delete(produto)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao deletar produto {id_produto}: {e}")
        return jsonify({'msg': 'Erro ao deletar produto no banco de dados.'}), 500
        
    return jsonify({'msg': 'Produto deletado com sucesso'}), 200

# POST - Enviar mensagem
@app.route('/mensagem', methods=['POST'])
@jwt_required()
def enviar_mensagem():
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400
        
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'Payload da requisição não pode ser vazio'}), 400

    if not all(k in data for k in ('conteudo_mensagem', 'id_solicitacao')):
        return jsonify({'msg': 'conteudo_mensagem e id_solicitacao são obrigatórios'}), 400

    solicitacao = Solicitacao.query.get(data['id_solicitacao'])
    if not solicitacao:
        return jsonify({'msg': 'Solicitação não encontrada'}), 404

    produto_desejado = Produto.query.get(solicitacao.id_produto_desejado)
    if not produto_desejado: 
         return jsonify({'msg': 'Produto da negociação não encontrado (erro de integridade)'}), 500

    # Verifica se o usuário atual é o solicitante ou o dono do produto desejado
    if current_user_id != solicitacao.id_usuario_solicitante and current_user_id != produto_desejado.id_usuario:
        return jsonify({'msg': 'Usuário não autorizado a interagir com esta negociação'}), 403
    
    # Verifica se a solicitação ainda está pendente para permitir o envio de mensagens
    if solicitacao.status != StatusSolicitacao.PENDENTE:
        return jsonify({'msg': f'Não é possível enviar mensagens em uma negociação com status "{solicitacao.status.value}". Apenas negociações pendentes aceitam novas mensagens.'}), 403

    nova_mensagem = Mensagem(
        conteudo_mensagem=data['conteudo_mensagem'],
        id_solicitacao=data['id_solicitacao'],
        id_usuario_remetente=current_user_id
    )
    try:
        db.session.add(nova_mensagem)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao enviar mensagem para solicitação {data['id_solicitacao']}: {e}")
        return jsonify({'msg': 'Erro ao salvar mensagem no banco de dados.'}), 500
        
    return jsonify(nova_mensagem.to_dict()), 201

# GET - Obter dados da tela de negociação
@app.route('/negociacao/<int:id_solicitacao>', methods=['GET'])
@jwt_required()
def obter_dados_negociacao(id_solicitacao):
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400
        
    solicitacao = Solicitacao.query.get(id_solicitacao)

    if not solicitacao:
        return jsonify({'msg': 'Negociação (Solicitação) não encontrada'}), 404

    produto_desejado = Produto.query.get(solicitacao.id_produto_desejado)
    if not produto_desejado: 
         return jsonify({'msg': 'Produto desejado na negociação não encontrado (erro de integridade)'}), 404

    if current_user_id != solicitacao.id_usuario_solicitante and current_user_id != produto_desejado.id_usuario:
        return jsonify({'msg': 'Acesso não autorizado a esta negociação'}), 403

    mensagens = Mensagem.query.filter_by(id_solicitacao=id_solicitacao).order_by(Mensagem.data_envio.asc()).all()
    
    resultado = {
        'solicitacao': solicitacao.to_dict(include_produtos_details=True),
        'mensagens': [msg.to_dict() for msg in mensagens],
    }
    return jsonify(resultado), 200

# POST - Criar solicitação (negociação)
@app.route('/solicitacao', methods=['POST'])
@jwt_required()
def criar_solicitacao():
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400
        
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'Payload da requisição não pode ser vazio'}), 400

    if not all(k in data for k in ('id_produto_desejado', 'tipo_solicitacao')):
        return jsonify({'msg': 'id_produto_desejado e tipo_solicitacao são obrigatórios'}), 400

    try:
        tipo_solicitacao = TipoDeInterese[data['tipo_solicitacao'].upper()]
    except KeyError:
        return jsonify({'msg': f"Valor inválido para 'tipo_solicitacao'. Use {', '.join([t.value for t in TipoDeInterese])}"}), 400

    try: 
        id_produto_desejado_int = int(data['id_produto_desejado'])
    except ValueError:
        return jsonify({'msg': 'ID do produto desejado inválido.'}), 400
    produto_desejado = Produto.query.get(id_produto_desejado_int)

    if not produto_desejado:
        return jsonify({'msg': 'Produto desejado não encontrado'}), 404
    
    if produto_desejado.id_usuario == current_user_id:
        return jsonify({'msg': 'Você não pode solicitar seu próprio produto'}), 400

    solicitacao_existente = Solicitacao.query.filter(
        Solicitacao.id_usuario_solicitante == current_user_id,
        Solicitacao.id_produto_desejado == id_produto_desejado_int,
        Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA])
    ).first()
    if solicitacao_existente:
        return jsonify({'msg': 'Você já possui uma solicitação ativa para este produto.'}), 409

    id_produto_ofertado_frontend = data.get('id_produto_ofertado')
    id_produto_ofertado_db = None 

    if tipo_solicitacao == TipoDeInterese.TROCA:
        if not id_produto_ofertado_frontend:
            return jsonify({'msg': 'id_produto_ofertado é obrigatório para solicitações de TROCA'}), 400
        try: 
            id_produto_ofertado_int = int(id_produto_ofertado_frontend)
        except ValueError:
            return jsonify({'msg': 'ID do produto ofertado inválido.'}), 400
        produto_ofertado = Produto.query.get(id_produto_ofertado_int)

        if not produto_ofertado:
            return jsonify({'msg': 'Produto ofertado não encontrado'}), 404
        if produto_ofertado.id_usuario != current_user_id:
            return jsonify({'msg': 'Você só pode ofertar seus próprios produtos'}), 403
        if produto_ofertado.id_produto == produto_desejado.id_produto: 
            return jsonify({'msg': 'Produto ofertado não pode ser o mesmo que o produto desejado'}),400
        id_produto_ofertado_db = produto_ofertado.id_produto
    elif id_produto_ofertado_frontend is not None: 
        return jsonify({'msg': 'id_produto_ofertado não deve ser enviado para solicitações de DOAÇÃO'}), 400

    nova_solicitacao = Solicitacao(
        id_usuario_solicitante=current_user_id,
        id_produto_desejado=id_produto_desejado_int,
        id_produto_ofertado=id_produto_ofertado_db, 
        tipo_solicitacao=tipo_solicitacao,
        status=StatusSolicitacao.PENDENTE
    )
    try:
        db.session.add(nova_solicitacao)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao criar solicitação: {e}")
        return jsonify({'msg': 'Erro ao criar solicitação no banco de dados.'}), 500
        
    return jsonify(nova_solicitacao.to_dict(include_produtos_details=True)), 201

# PUT - Aceitar/Rejeitar solicitação (negociação)
@app.route('/solicitacao/<int:id_solicitacao>/acao', methods=['PUT'])
@jwt_required()
def acao_solicitacao(id_solicitacao):
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400
        
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'Payload da requisição não pode ser vazio'}), 400

    if 'status' not in data:
        return jsonify({'msg': "Campo 'status' (APROVADA ou RECUSADA) é obrigatório"}), 400

    try:
        novo_status_str = data['status'].upper()
        novo_status = StatusSolicitacao[novo_status_str]
        if novo_status not in [StatusSolicitacao.APROVADA, StatusSolicitacao.RECUSADA]:
            raise KeyError 
    except KeyError:
        return jsonify({'msg': "Status inválido. Use 'APROVADA' ou 'RECUSADA'."}), 400

    solicitacao = Solicitacao.query.get(id_solicitacao)
    if not solicitacao:
        return jsonify({'msg': 'Solicitação não encontrada'}), 404

    produto_desejado = Produto.query.get(solicitacao.id_produto_desejado)
    if not produto_desejado or produto_desejado.id_usuario != current_user_id:
        return jsonify({'msg': 'Ação não permitida. Você não é o proprietário do produto desejado.'}), 403

    if solicitacao.status != StatusSolicitacao.PENDENTE:
        return jsonify({'msg': f'Ação não permitida. Solicitação não está PENDENTE (status atual: {solicitacao.status.value})'}), 409

    solicitacao.status = novo_status
    if novo_status == StatusSolicitacao.APROVADA:
        nova_transacao = Transacao()
        db.session.add(nova_transacao)
        solicitacao.transacao_obj = nova_transacao

        outras_solicitacoes_produto_desejado = Solicitacao.query.filter(
            Solicitacao.id_produto_desejado == solicitacao.id_produto_desejado,
            Solicitacao.id_solicitacao != solicitacao.id_solicitacao, 
            Solicitacao.status == StatusSolicitacao.PENDENTE
        ).all()
        for s_outra in outras_solicitacoes_produto_desejado:
            s_outra.status = StatusSolicitacao.RECUSADA
        
        if solicitacao.id_produto_ofertado: 
            outras_solicitacoes_produto_ofertado = Solicitacao.query.filter(
                ( (Solicitacao.id_produto_desejado == solicitacao.id_produto_ofertado) | \
                  (Solicitacao.id_produto_ofertado == solicitacao.id_produto_ofertado) ),
                Solicitacao.id_solicitacao != solicitacao.id_solicitacao, 
                Solicitacao.status == StatusSolicitacao.PENDENTE
            ).all()
            for s_outra in outras_solicitacoes_produto_ofertado:
                s_outra.status = StatusSolicitacao.RECUSADA
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao processar ação para solicitação {id_solicitacao}: {e}")
        return jsonify({'msg': 'Erro ao processar ação da solicitação no banco de dados.'}), 500
        
    return jsonify(solicitacao.to_dict(include_produtos_details=True)), 200

# DELETE - Cancelar solicitação
@app.route('/solicitacao/<int:id_solicitacao>', methods=['DELETE'])
@jwt_required()
def cancelar_solicitacao(id_solicitacao):
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400
        
    solicitacao = Solicitacao.query.get(id_solicitacao)

    if not solicitacao:
        return jsonify({'msg': 'Solicitação não encontrada'}), 404

    if solicitacao.id_usuario_solicitante != current_user_id:
        return jsonify({'msg': 'Você não pode cancelar esta solicitação.'}), 403

    if solicitacao.status != StatusSolicitacao.PENDENTE:
        return jsonify({'msg': f'Solicitação não pode ser cancelada pois seu status é {solicitacao.status.value}.'}), 409
    
    solicitacao.status = StatusSolicitacao.CANCELADA
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao cancelar solicitação {id_solicitacao}: {e}")
        return jsonify({'msg': 'Erro ao cancelar solicitação no banco de dados.'}), 500
        
    return jsonify({'msg': 'Solicitação cancelada com sucesso'}), 200


@app.route('/')
def hello():
    return "API de Trocas e Doações está funcionando!"

def create_tables():
    with app.app_context():
        db.create_all()
        print("Tabelas criadas (se não existiam)!")

        if Categoria.query.count() == 0:
            print("Adicionando categorias de exemplo...")
            categorias_exemplo = [
                {'nome_categoria': 'Eletrônicos', 'descricao': 'Dispositivos eletrônicos e acessórios'},
                {'nome_categoria': 'Livros', 'descricao': 'Livros de diversos gêneros'},
                {'nome_categoria': 'Móveis', 'descricao': 'Móveis para casa e escritório'},
                {'nome_categoria': 'Roupas', 'descricao': 'Vestuário masculino, feminino e infantil'},
                {'nome_categoria': 'Brinquedos', 'descricao': 'Brinquedos para todas as idades'}
            ]
            for cat_data in categorias_exemplo:
                db.session.add(Categoria(**cat_data))
            try:
                db.session.commit()
                print("Categorias de exemplo adicionadas.")
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Erro ao adicionar categorias de exemplo: {e}")


if __name__ == '__main__':
    # create_tables() 
    app.run(debug=True)