import os
from datetime import timedelta, datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from sqlalchemy.orm import joinedload, selectinload 
from sqlalchemy import or_, and_
from dotenv import load_dotenv
from flask_cors import CORS
import uuid

from models import (
    db, Usuario, Produto, Imagem, Categoria, Mensagem,
    Solicitacao, Transacao, EnderecoUsuario,
    StatusSolicitacao, StatusProduto, TipoDeInterese, tabela_produto_categoria,
    SolicitacaoProdutoOfertado
)

# Configuracão
load_dotenv(dotenv_path='./venv/.env')
app = Flask(__name__, static_url_path='', static_folder='uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
CORS(app)

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
    if not all(k in data for k in ('nome_usuario', 'email', 'senha', 'telefone', 'data_nascimento', 'cep', 'bairro', 'rua', 'numero', 'cidade', 'estado')):
        return jsonify({'msg': 'Campos obrigatórios faltando: nome_usuario, email, senha, telefone, data_nascimento, cep, bairro, rua, numero, cidade, estado'}), 400

    # Validação de e-mail único
    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({'msg': 'Email já cadastrado'}), 409

    # Validação de CPF único (se informado)
    if data.get('cpf'):
        if Usuario.query.filter_by(cpf=data['cpf']).first():
            return jsonify({'msg': 'CPF já cadastrado'}), 409

    data_nasc = parse_date(data.get('data_nascimento'))
    if not data_nasc:
        return jsonify({'msg': 'Formato de data_nascimento inválido. Use YYYY-MM-DD.'}), 400

    # Criar o usuário
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
        db.session.flush()  # Garante que o ID do usuário seja gerado antes de salvar o endereço

        # Criar o endereço associado ao usuário
        novo_endereco = EnderecoUsuario(
            cep=data['cep'],
            bairro=data['bairro'],
            rua=data['rua'],
            numero=data['numero'],
            complemento=data.get('complemento'),
            cidade=data['cidade'],
            estado=data['estado'],
            id_usuario=novo_usuario.id_usuario
        )
        db.session.add(novo_endereco)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao salvar usuário: {e}") 
        return jsonify({'msg': 'Erro ao salvar usuário no banco de dados.'}), 500
    
    return jsonify({'msg': 'Usuário cadastrado com sucesso!', 
                    'id_usuario': novo_usuario.id_usuario,
                    'nome_usuario': novo_usuario.nome_usuario}), 201

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
    current_user_id = get_current_user_id_from_token()

    # Subconsulta para IDs de produtos desejados em solicitações PENDENTES ou APROVADAS
    sq_desejados = db.select(Solicitacao.id_produto_desejado.distinct().label("produto_id"))\
        .where(Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA]))\
        .where(Solicitacao.id_produto_desejado.isnot(None))

    # Subconsulta para IDs de produtos ofertados em solicitações PENDENTES ou APROVADAS (tabela de relacionamento)
    sq_ofertados = db.select(SolicitacaoProdutoOfertado.id_produto.distinct().label("produto_id"))\
        .join(Solicitacao, SolicitacaoProdutoOfertado.id_solicitacao == Solicitacao.id_solicitacao)\
        .where(Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA]))

    ids_desejados_result = db.session.execute(sq_desejados).scalars().all()
    ids_ofertados_result = db.session.execute(sq_ofertados).scalars().all()
    todos_ids_produtos_em_negociacao = list(set(ids_desejados_result + ids_ofertados_result))

    # Filtra produtos que não são do usuário logado e não estão em negociação
    query = Produto.query.filter(Produto.id_usuario != current_user_id)
    if todos_ids_produtos_em_negociacao:
        query = query.filter(Produto.id_produto.notin_(todos_ids_produtos_em_negociacao))
    produtos_ativos = query.all()

    return jsonify([produto.to_dict(include_owner=True) for produto in produtos_ativos]), 200

# GET - Obter todos produtos vinculados ao ID do usuário (logado)
@app.route('/produtos/usuario', methods=['GET'])
@jwt_required()
def obter_meus_produtos_gerenciaveis(): # Nome pode ser mais descritivo
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400

    # Subconsulta: IDs dos produtos do usuário que foram DESEJADOS e a negociação APROVADA
    # (ou seja, o usuário "perdeu" este produto porque alguém o solicitou e ele aprovou)
    stmt_desejados_aprovados = db.select(Produto.id_produto)\
        .join(Solicitacao, Produto.id_produto == Solicitacao.id_produto_desejado)\
        .where(Produto.id_usuario == current_user_id, Solicitacao.status == StatusSolicitacao.APROVADA)\
        .distinct()
    ids_desejados_aprovados = {row[0] for row in db.session.execute(stmt_desejados_aprovados).fetchall()}

    # Subconsulta: IDs dos produtos do usuário que foram OFERTADOS e a negociação APROVADA
    # (ou seja, o usuário "perdeu" este produto porque o ofertou em uma troca bem-sucedida)
    stmt_ofertados_aprovados = db.select(Produto.id_produto)\
        .join(SolicitacaoProdutoOfertado, Produto.id_produto == SolicitacaoProdutoOfertado.id_produto)\
        .join(Solicitacao, SolicitacaoProdutoOfertado.id_solicitacao == Solicitacao.id_solicitacao)\
        .where(Produto.id_usuario == current_user_id, Solicitacao.status == StatusSolicitacao.APROVADA)\
        .distinct()
    ids_ofertados_aprovados = {row[0] for row in db.session.execute(stmt_ofertados_aprovados).fetchall()}

    ids_produtos_ja_transacionados = ids_desejados_aprovados.union(ids_ofertados_aprovados)

    # Buscar produtos do usuário que NÃO estão na lista de transacionados
    query_produtos_gerenciaveis = Produto.query.filter(
        Produto.id_usuario == current_user_id,
        Produto.id_produto.notin_(ids_produtos_ja_transacionados)
    ).options( # Eager loading para performance
        selectinload(Produto.imagens),
        selectinload(Produto.categoria),
        selectinload(Produto.solicitacoes_para_este_produto) # Para pegar solicitações pendentes
    )
    
    produtos_gerenciaveis = query_produtos_gerenciaveis.all()

    resultado_final = []
    for produto in produtos_gerenciaveis:
        produto_dict = produto.to_dict(include_owner=True, include_imagens=True, include_categoria=True)
        
        # Adicionar informações sobre solicitações PENDENTES para este produto
        # (onde ele é o produto desejado)
        solicitacoes_pendentes = [
            s.to_dict() for s in produto.solicitacoes_para_este_produto 
            if s.status == StatusSolicitacao.PENDENTE
        ]
        produto_dict['solicitacoes_pendentes_nele'] = solicitacoes_pendentes
        resultado_final.append(produto_dict)
        
    return jsonify(resultado_final), 200

# GET - Obter todas as negociacoes vinculadas ao ID do usuário (logado)
@app.route('/usuario/negociacoes', methods=['GET'])
@jwt_required()
def obter_minhas_negociacoes():
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400

    # Usamos db.or_ para combinar as duas condições
    negociacoes_query = Solicitacao.query.join(
        Produto, Solicitacao.id_produto_desejado == Produto.id_produto
    ).filter(
        db.or_( # Lembre de importar or_ de sqlalchemy ou usar db.or_
            Solicitacao.id_usuario_solicitante == current_user_id, # Ele é o solicitante
            Produto.id_usuario == current_user_id                  # Ele é o dono do produto desejado
        )
    ).options(
        # Eager loading para carregar todos os dados relacionados eficientemente
        selectinload(Solicitacao.usuario_solicitante_obj),
        selectinload(Solicitacao.produto_desejado_obj).selectinload(Produto.proprietario),
        selectinload(Solicitacao.produto_desejado_obj).selectinload(Produto.imagens),
        selectinload(Solicitacao.produto_desejado_obj).selectinload(Produto.categoria),
        selectinload(Solicitacao.produtos_ofertados).selectinload(Produto.imagens),
        selectinload(Solicitacao.produtos_ofertados).selectinload(Produto.proprietario), # Se precisar do dono dos produtos ofertados
        selectinload(Solicitacao.produtos_ofertados).selectinload(Produto.categoria)  # E categoria dos ofertados
    ).order_by(Solicitacao.data_solicitacao.desc())
    
    negociacoes = negociacoes_query.all()
    
    # O método to_dict da Solicitacao já deve incluir 'include_produtos_details=True'
    # para trazer os detalhes dos produtos envolvidos.
    # Certifique-se que Solicitacao.to_dict() e Produto.to_dict() carregam
    # as informações do proprietário do produto e do solicitante.
    resultado = [s.to_dict(include_produtos_details=True) for s in negociacoes]
    
    return jsonify(resultado), 200

# GET - Obter produto pelo ID
@app.route('/produto/<int:id_produto>', methods=['GET'])
@jwt_required()
def obter_produto(id_produto):
    current_user_id = get_current_user_id_from_token()

    stmt = db.select(Produto).options(
        joinedload(Produto.proprietario),
        selectinload(Produto.imagens),
        selectinload(Produto.categoria)
    ).where(Produto.id_produto == id_produto)
    produto = db.session.execute(stmt).scalar_one_or_none()
    
    if not produto:
        return jsonify({'msg': 'Produto não encontrado'}), 404

    produto_dict = produto.to_dict(include_owner=True, include_categoria=True, include_imagens=True)

    # Busca a solicitação do usuário logado para este produto (se houver)
    solicitacao = Solicitacao.query.filter_by(
        id_usuario_solicitante=current_user_id,
        id_produto_desejado=id_produto
    ).order_by(Solicitacao.id_solicitacao.desc()).first()
    if solicitacao:
        produto_dict['status_solicitacao'] = solicitacao.status.value
    else:
        produto_dict['status_solicitacao'] = None

    return jsonify(produto_dict), 200

# POST - Criar produto
@app.route('/produto', methods=['POST'])
@jwt_required()
def criar_produto():
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400

    # Recebe dados do formulário
    nome_produto = request.form.get('nome_produto')
    descricao = request.form.get('descricao')
    id_categoria = request.form.get('id_categoria', type=int)
    quantidade = request.form.get('quantidade', type=int)
    status = request.form.get('status')

    if not nome_produto or not descricao or not id_categoria or not quantidade or not status:
        return jsonify({'msg': 'Campos nome_produto, descricao, id_categoria, quantidade e status são obrigatórios'}), 400

    try:
        status_produto = StatusProduto[status.upper()]
    except KeyError:
        return jsonify({'msg': f"Valor inválido para 'status'. Use NOVO ou USADO."}), 400

    novo_produto = Produto(
        nome_produto=nome_produto,
        descricao=descricao,
        id_usuario=current_user_id,
        id_categoria=id_categoria,
        quantidade=quantidade,
        status=status_produto
    )
    db.session.add(novo_produto)
    db.session.flush()  # Para garantir o ID do produto

    # Salvar imagens
    imagens = request.files.getlist('images')
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    for img in imagens:
        if img and img.filename:
            ext = os.path.splitext(img.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            filepath = os.path.join(upload_folder, filename)
            img.save(filepath)
            nova_imagem = Imagem(
                url_imagem=f'uploads/{filename}',
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

    # Suporte a JSON ou multipart/form-data
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        nome_produto = request.form.get('nome_produto')
        descricao = request.form.get('descricao')
        quantidade = request.form.get('quantidade', type=int)
        id_categoria = request.form.get('id_categoria', type=int)
        status = request.form.get('status')
        imagens = request.files.getlist('images')
    else:
        data = request.get_json()
        if not data:
            return jsonify({'msg': 'Payload da requisição não pode ser vazio'}), 400
        nome_produto = data.get('nome_produto')
        descricao = data.get('descricao')
        quantidade = data.get('quantidade')
        id_categoria = data.get('id_categoria')
        status = data.get('status')
        imagens = []

    if nome_produto:
        produto.nome_produto = nome_produto
    if descricao:
        produto.descricao = descricao
    if quantidade is not None:
        produto.quantidade = quantidade
    if id_categoria:
        produto.id_categoria = id_categoria
    if status:
        try:
            produto.status = StatusProduto[status.upper()]
        except KeyError:
            return jsonify({'msg': "Valor inválido para 'status'. Use NOVO ou USADO."}), 400

    # Se vierem novas imagens, remove as antigas e salva as novas
    if imagens and any(img.filename for img in imagens):
        # Remove imagens antigas do banco e do disco
        for img in produto.imagens:
            img_path = os.path.join(os.getcwd(), img.url_imagem)
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception as e:
                    app.logger.error(f"Erro ao remover arquivo {img_path}: {e}")
            db.session.delete(img)
        db.session.flush()
        # Salva novas imagens
        upload_folder = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        for img in imagens:
            if img and img.filename:
                ext = os.path.splitext(img.filename)[1]
                filename = f"{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(upload_folder, filename)
                img.save(filepath)
                nova_imagem = Imagem(
                    url_imagem=f'uploads/{filename}',
                    produto=produto
                )
                db.session.add(nova_imagem)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao alterar produto {id_produto}: {e}")
        return jsonify({'msg': 'Erro ao atualizar produto no banco de dados.'}), 500

    return jsonify(produto.to_dict(include_owner=True, include_categoria=True, include_imagens=True)), 200

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

    solicitacao_como_desejado_ativa = Solicitacao.query.filter(
    Solicitacao.id_produto_desejado == id_produto,
    Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA])
    ).first()

    # Verifica se o produto está ofertado em alguma solicitação ativa
    solicitacao_como_ofertado_ativa = db.session.query(Solicitacao).join(SolicitacaoProdutoOfertado).\
        filter(SolicitacaoProdutoOfertado.id_produto == id_produto,
            Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA])
        ).first()

    if solicitacao_como_desejado_ativa or solicitacao_como_ofertado_ativa:
        return jsonify({'msg': 'Produto não pode ser deletado pois está envolvido em negociações ativas.'}), 409

    # Remove imagens do diretório físico
    for img in produto.imagens:
        img_path = os.path.join(os.getcwd(), img.url_imagem)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                app.logger.error(f"Erro ao remover arquivo {img_path}: {e}")

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
    if solicitacao.status not in [StatusSolicitacao.PENDENTE, StatusSolicitacao.PROCESSANDO]:
        return jsonify({'msg': f'Não é possível enviar mensagens em uma negociação com status "{solicitacao.status.value}". Apenas negociações PROCESSANDO ou PENDENTE aceitam novas mensagens.'}), 403

    nova_mensagem = Mensagem(
        conteudo_mensagem=data['conteudo_mensagem'],
        id_solicitacao=data['id_solicitacao'],
        id_usuario=current_user_id
    )
    try:
        db.session.add(nova_mensagem)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao enviar mensagem para solicitação {data['id_solicitacao']}: {e}")
        return jsonify({'msg': 'Erro ao salvar mensagem no banco de dados.'}), 500
        
    return jsonify(nova_mensagem.to_dict()), 201

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

    # Descobre o tipo da solicitação pela categoria do produto desejado
    tipo_solicitacao = produto_desejado.categoria.nome_categoria.upper()

    produtos_ofertados_ids = data.get('id_produto_ofertado', [])

    print(f"Tipo de solicitação: {tipo_solicitacao}")
    print(f"Produtos ofertados: {produtos_ofertados_ids}")

    if tipo_solicitacao == 'TROCA':
        # Aceita tanto int quanto lista
        if not produtos_ofertados_ids:
            return jsonify({'msg': 'id_produto_ofertado é obrigatório para solicitações de TROCA'}), 400
        if isinstance(produtos_ofertados_ids, int):
            produtos_ofertados_ids = [produtos_ofertados_ids]
        if not isinstance(produtos_ofertados_ids, list):
            return jsonify({'msg': 'id_produto_ofertado deve ser uma lista de IDs'}), 400
        # Validação dos produtos ofertados
        for id_produto in produtos_ofertados_ids:
            produto_ofertado = Produto.query.get(id_produto)
            if not produto_ofertado:
                return jsonify({'msg': f'Produto ofertado {id_produto} não encontrado'}), 404
            if produto_ofertado.id_usuario != current_user_id:
                return jsonify({'msg': 'Você só pode ofertar seus próprios produtos'}), 403
            if produto_ofertado.id_produto == produto_desejado.id_produto: 
                return jsonify({'msg': 'Produto ofertado não pode ser o mesmo que o produto desejado'}),400
    elif produtos_ofertados_ids:
        return jsonify({'msg': 'id_produto_ofertado não deve ser enviado para solicitações de DOAÇÃO'}), 400

    nova_solicitacao = Solicitacao(
        id_usuario_solicitante=current_user_id,
        id_produto_desejado=id_produto_desejado_int,
        status=StatusSolicitacao.PENDENTE
    )
    try:
        db.session.add(nova_solicitacao)
        db.session.flush()  # Garante o ID da solicitação

        # Se for troca, salva os produtos ofertados na tabela de relacionamento
        if tipo_solicitacao == TipoDeInterese.TROCA:
            for id_produto in produtos_ofertados_ids:
                rel = SolicitacaoProdutoOfertado(
                    id_solicitacao=nova_solicitacao.id_solicitacao,
                    id_produto=id_produto
                )
                db.session.add(rel)

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

        # Recusa outras solicitações pendentes para o mesmo produto desejado
        outras_solicitacoes_produto_desejado = Solicitacao.query.filter(
            Solicitacao.id_produto_desejado == solicitacao.id_produto_desejado,
            Solicitacao.id_solicitacao != solicitacao.id_solicitacao, 
            Solicitacao.status == StatusSolicitacao.PENDENTE
        ).all()
        for s_outra in outras_solicitacoes_produto_desejado:
            s_outra.status = StatusSolicitacao.RECUSADA
            
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao processar ação para solicitação {id_solicitacao}: {e}")
        return jsonify({'msg': 'Erro ao processar ação da solicitação no banco de dados.'}), 500

    if novo_status == StatusSolicitacao.APROVADA and hasattr(solicitacao, "produtos_ofertados"):
        # Só para troca: atualiza produtos ofertados se enviados
        produtos_ofertados_ids = data.get('id_produto_ofertado', [])
        if produtos_ofertados_ids:
            # Remove antigos
            SolicitacaoProdutoOfertado.query.filter_by(id_solicitacao=solicitacao.id_solicitacao).delete()
            # Adiciona novos
            for id_produto in produtos_ofertados_ids:
                rel = SolicitacaoProdutoOfertado(
                    id_solicitacao=solicitacao.id_solicitacao,
                    id_produto=id_produto
                )
                db.session.add(rel)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao atualizar produtos ofertados para solicitação {id_solicitacao}: {e}")
        return jsonify({'msg': 'Erro ao atualizar produtos ofertados no banco de dados.'}), 500
        
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

# PUT - Marcar solicitação como PENDENTE
@app.route('/solicitacao/<int:id_solicitacao>/pendente', methods=['PUT'])
@jwt_required()
def marcar_solicitacao_pendente(id_solicitacao):
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400

    solicitacao = Solicitacao.query.get(id_solicitacao)
    if not solicitacao:
        return jsonify({'msg': 'Solicitação não encontrada'}), 404

    if solicitacao.id_usuario_solicitante != current_user_id:
        return jsonify({'msg': 'Você não pode alterar esta solicitação.'}), 403

    if solicitacao.status != StatusSolicitacao.PROCESSANDO:
        return jsonify({'msg': f'Só é possível ativar solicitações com status PROCESSANDO. Status atual: {solicitacao.status.value}'}), 409

    data = request.get_json() or {}
    produtos_ofertados_ids = data.get('id_produto_ofertado', [])

    # Só exige produtos ofertados se for troca
    tipo_solicitacao = solicitacao.produto_desejado_obj.categoria.nome_categoria.upper()
    if tipo_solicitacao == 'TROCA':
        if not produtos_ofertados_ids:
            return jsonify({'msg': 'id_produto_ofertado é obrigatório para solicitações de TROCA'}), 400
        if isinstance(produtos_ofertados_ids, int):
            produtos_ofertados_ids = [produtos_ofertados_ids]
        if not isinstance(produtos_ofertados_ids, list):
            return jsonify({'msg': 'id_produto_ofertado deve ser uma lista de IDs'}), 400

        # Remove antigos
        SolicitacaoProdutoOfertado.query.filter_by(id_solicitacao=solicitacao.id_solicitacao).delete()
        # Adiciona novos
        for id_produto in produtos_ofertados_ids:
            produto_ofertado = Produto.query.get(id_produto)
            if not produto_ofertado:
                return jsonify({'msg': f'Produto ofertado {id_produto} não encontrado'}), 404
            if produto_ofertado.id_usuario != current_user_id:
                return jsonify({'msg': 'Você só pode ofertar seus próprios produtos'}), 403
            if produto_ofertado.id_produto == solicitacao.id_produto_desejado:
                return jsonify({'msg': 'Produto ofertado não pode ser o mesmo que o produto desejado'}), 400
            rel = SolicitacaoProdutoOfertado(
                id_solicitacao=solicitacao.id_solicitacao,
                id_produto=id_produto
            )
            db.session.add(rel)

    # Atualiza status
    solicitacao.status = StatusSolicitacao.PENDENTE
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao ativar solicitação {id_solicitacao}: {e}")
        return jsonify({'msg': 'Erro ao atualizar solicitação no banco de dados.'}), 500

    return jsonify({'msg': 'Solicitação ativada com sucesso!', 'solicitacao': solicitacao.to_dict(include_produtos_details=True)}), 200

@app.route('/')
def hello():
    return "API de Trocas e Doações está funcionando!"

def create_tables():
    with app.app_context():
        db.create_all()
        print("Tabelas criadas (se não existiam)!")


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

# GET - Obter dados da tela de negociação por produto
@app.route('/negociacao/<int:id_produto>', methods=['GET'])
@jwt_required()
def obter_dados_negociacao_por_produto(id_produto):
    try:
        current_user_id = get_current_user_id_from_token()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400

    produto = Produto.query.get(id_produto)
    if not produto:
        return jsonify({'msg': 'Produto não encontrado'}), 404

    solicitacao = Solicitacao.query.filter(
        Solicitacao.id_produto_desejado == id_produto,
        Solicitacao.status.in_([
            StatusSolicitacao.PROCESSANDO,
            StatusSolicitacao.PENDENTE,
            StatusSolicitacao.APROVADA
        ])
    ).order_by(Solicitacao.id_solicitacao.desc()).first()

    # Se não existe solicitação e o usuário logado NÃO for o dono do produto, cria uma solicitação PROCESSANDO
    if not solicitacao and produto.id_usuario != current_user_id:
        solicitacao = Solicitacao(
            id_usuario_solicitante=current_user_id,
            id_produto_desejado=id_produto,
            status=StatusSolicitacao.PROCESSANDO
        )
        db.session.add(solicitacao)
        db.session.commit()
        solicitacao = Solicitacao.query.get(solicitacao.id_solicitacao)

    if not solicitacao:
        return jsonify({'msg': 'Negociação não encontrada'}), 404

    # Só o solicitante ou o dono do produto pode acessar
    if current_user_id != solicitacao.id_usuario_solicitante and current_user_id != produto.id_usuario:
        return jsonify({'msg': 'Acesso não autorizado a esta negociação'}), 403

    # Só permite visualizar se a solicitação está PROCESSANDO, PENDENTE ou APROVADA
    if solicitacao.status not in [StatusSolicitacao.PROCESSANDO, StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA]:
        return jsonify({'msg': 'Esta negociação foi encerrada e não pode mais ser visualizada.'}), 403

    mensagens = Mensagem.query.filter_by(id_solicitacao=solicitacao.id_solicitacao).order_by(Mensagem.data_envio.asc()).all()

    # Obtém o endereço do proprietário do produto, se disponível
    proprietario = produto.proprietario
    endereco = None
    if proprietario:
        # Força o carregamento dos endereços
        enderecos = getattr(proprietario, 'enderecos_usuario', [])
        if enderecos:
            endereco_obj = enderecos[0]
            endereco = {
                'cep': endereco_obj.cep,
                'bairro': endereco_obj.bairro,
                'rua': endereco_obj.rua,
                'numero': endereco_obj.numero,
                'complemento': endereco_obj.complemento,
                'cidade': endereco_obj.cidade,
                'estado': endereco_obj.estado
            }

    produto_dict = produto.to_dict(include_owner=True, include_categoria=True, include_imagens=True)
    produto_dict['endereco'] = endereco

    resultado = {
        'solicitacao': solicitacao.to_dict(include_produtos_details=True),
        'mensagens': [msg.to_dict() for msg in mensagens],
        'produto_endereco': endereco  # opcional, se quiser fora do produto
    }
    resultado['solicitacao']['produto_desejado']['endereco'] = endereco

    return jsonify(resultado), 200

# GET - Obter dados da tela de negociação por solicitação
@app.route('/negociacao/solicitacao/<int:id_solicitacao>', methods=['GET'])
@jwt_required()
def obter_dados_negociacao_por_solicitacao(id_solicitacao):
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

if __name__ == '__main__':
    # create_tables() 
    app.run(debug=True)
