# routes/negotiation_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Importa db e modelos do arquivo models.py
# Certifique-se de que o arquivo models.py está no diretório correto e acessível
from camadaModelo import db, Negociacao, Mensagem, StatusNegociacao, Produto, Usuario, StatusProduto # Importa Usuario e Produto para validações e dados

# Cria um Blueprint para as rotas de negociação
# O prefixo '/negociacoes' será adicionado a todas as rotas definidas neste Blueprint
negociacao = Blueprint('negotiation', __name__, url_prefix='/negociacoes')

# --- Rotas de Negociação ---

@negociacao.route('/', methods=['POST'])
@jwt_required() # Protege esta rota, exigindo um JWT válido
def create_negociacao():
    """
    Endpoint para criar uma nova negociação (solicitação de troca ou doação).
    Requer autenticação via JWT.
    Espera um corpo de requisição JSON com:
    'produto_principal_id': ID do produto que está sendo solicitado.
    'tipo': 'Troca' ou 'Doacao'.
    'produtos_troca_ids': Lista de IDs de produtos oferecidos para troca (obrigatório se tipo='Troca').
    """
    try:
        # Obtém o ID do usuário logado a partir do JWT
        current_user_id = get_jwt_identity()

        # Obtém os dados JSON do corpo da requisição
        data = request.get_json()

        # Valida se os campos obrigatórios estão presentes
        if not data or 'produto_principal_id' not in data or 'tipo' not in data:
            return jsonify({'erro': 'Campos "produto_principal_id" e "tipo" são obrigatórios.'}), 400 # Bad Request

        produto_principal_id = data.get('produto_principal_id')
        tipo = data.get('tipo')
        # Obtém a lista de IDs de produtos de troca, padrão para lista vazia se não fornecido
        produtos_troca_ids = data.get('produtos_troca_ids', [])

        # Valida o tipo de negociação
        if tipo not in ['Troca', 'Doacao']:
            return jsonify({'erro': 'Tipo de negociação inválido. Use "Troca" ou "Doacao".'}), 400 # Bad Request

        # Valida se produtos de troca foram fornecidos para negociações do tipo 'Troca'
        if tipo == 'Troca' and not produtos_troca_ids:
            return jsonify({'erro': 'Para negociações do tipo "Troca", "produtos_troca_ids" é obrigatório e não pode ser vazio.'}), 400 # Bad Request

        # Busca o produto principal no banco de dados
        produto_principal = Produto.query.get(produto_principal_id)
        if produto_principal is None:
            return jsonify({'erro': 'Produto principal não encontrado.'}), 404 # Not Found

        # Verifica se o usuário logado não está tentando negociar seu próprio produto principal
        if produto_principal.usuario_id == current_user_id:
             return jsonify({'erro': 'Você não pode iniciar uma negociação para seu próprio produto.'}), 400 # Bad Request

        # Opcional: Verifica se já existe uma negociação pendente para este produto principal e este solicitante
        status_pendente_neg = StatusNegociacao.query.filter_by(nome='Pendente').first()
        if status_pendente_neg: # Verifica se o status 'Pendente' existe
             negociacao_existente = Negociacao.query.filter_by(
                 produto_principal_id=produto_principal_id,
                 solicitante_id=current_user_id,
                 status_id=status_pendente_neg.id
             ).first()
             if negociacao_existente:
                 return jsonify({'erro': 'Já existe uma negociação pendente sua para este produto.'}), 409 # Conflict


        # Busca o status inicial da negociação ('Pendente') no banco de dados
        # É crucial que este status exista no DB
        status_pendente = StatusNegociacao.query.filter_by(nome='Pendente').first()
        if status_pendente is None:
             # Isso indica um problema na configuração inicial do banco de dados (status 'Pendente' faltando)
             print("Erro: Status 'Pendente' para negociação não encontrado no DB.")
             return jsonify({'erro': 'Erro interno do servidor: Status de negociação inicial não configurado.'}), 500 # Internal Server Error

        # Cria uma nova instância do modelo Negociacao
        nova_negociacao = Negociacao(
            produto_principal_id=produto_principal.id,
            solicitante_id=current_user_id,
            proprietario_id=produto_principal.usuario_id, # O proprietário do produto principal é o outro usuário envolvido
            tipo=tipo,
            status_id=status_pendente.id # Define o status inicial como Pendente
        )

        # Se o tipo de negociação for 'Troca', busca e associa os produtos de troca
        if tipo == 'Troca':
            produtos_troca = Produto.query.filter(Produto.id.in_(produtos_troca_ids)).all()
            # Validação: Verifica se todos os IDs de produtos de troca fornecidos foram encontrados
            if len(produtos_troca) != len(produtos_troca_ids):
                 return jsonify({'erro': 'Um ou mais produtos de troca não foram encontrados.'}), 404 # Not Found

            # Opcional: Validação: Verifica se os produtos de troca pertencem ao usuário solicitante
            if any(p.usuario_id != current_user_id for p in produtos_troca):
                 return jsonify({'erro': 'Você só pode oferecer seus próprios produtos para troca.'}), 403 # Forbidden

            # Associa a lista de produtos de troca à negociação
            nova_negociacao.produtos_troca = produtos_troca


        # Adiciona a nova negociação à sessão do banco de dados e salva
        db.session.add(nova_negociacao)
        db.session.commit()

        # Opcional: Mudar o status do produto principal para 'Em Negociação' após a criação da negociação
        status_em_negociacao_produto = StatusProduto.query.filter_by(nome='Em Negociação').first()
        if status_em_negociacao_produto and produto_principal.status_id != status_em_negociacao_produto.id:
             produto_principal.status_id = status_em_negociacao_produto.id
             db.session.commit() # Salva a alteração no status do produto


        # Serializa a negociação criada para a resposta JSON
        negociacao_json = {
            'id': nova_negociacao.id,
            'produto_principal_id': nova_negociacao.produto_principal_id,
            'solicitante_id': nova_negociacao.solicitante_id,
            'proprietario_id': nova_negociacao.proprietario_id,
            'tipo': nova_negociacao.tipo,
            'status': nova_negociacao.status.nome if nova_negociacao.status else 'Desconhecido', # Inclui o nome do status
            'data_criacao': nova_negociacao.data_criacao.isoformat(), # Formato ISO para data/hora
            'data_atualizacao': nova_negociacao.data_atualizacao.isoformat() # Formato ISO para data/hora
        }

        # Retorna a negociação criada como JSON com status 201
        return jsonify(negociacao_json), 201 # Created

    except Exception as e:
        # Em caso de erro, desfaz a transação no banco de dados
        db.session.rollback()
        # Loga o erro no servidor
        print(f"Erro ao criar negociação: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao criar a negociação.'}), 500 # Internal Server Error

@negociacao.route('/<int:negociacao_id>/mensagens', methods=['POST'])
@jwt_required() # Protege esta rota, exigindo um JWT válido
def send_message(negociacao_id):
    """
    Endpoint para enviar uma nova mensagem em uma negociação específica.
    Requer autenticação via JWT.
    Espera um corpo de requisição JSON com o campo 'conteudo'.
    """
    try:
        # Obtém o ID do usuário logado a partir do JWT
        current_user_id = get_jwt_identity()

        # Busca a negociação pelo ID fornecido na URL
        negociacao = Negociacao.query.get(negociacao_id)
        if negociacao is None:
            return jsonify({'erro': 'Negociação não encontrada.'}), 404 # Not Found

        # Verifica se o usuário logado participa desta negociação (é o solicitante ou o proprietário)
        if current_user_id != negociacao.solicitante_id and current_user_id != negociacao.proprietario_id:
             return jsonify({'erro': 'Você não participa desta negociação.'}), 403 # Forbidden

        # Opcional: Permitir envio de mensagens apenas em status específicos da negociação (ex: Pendente, Aceita)
        status_pendente = StatusNegociacao.query.filter_by(nome='Pendente').first()
        status_aceita = StatusNegociacao.query.filter_by(nome='Aceita').first()
        # Verifica se os status existem antes de comparar
        if status_pendente and status_aceita and negociacao.status_id not in [status_pendente.id, status_aceita.id]:
             return jsonify({'erro': f'Não é possível enviar mensagens nesta negociação com status "{negociacao.status.nome}".'}), 400 # Bad Request


        # Obtém os dados JSON do corpo da requisição
        data = request.get_json()

        # Valida se o campo 'conteudo' está presente e não está vazio
        if not data or 'conteudo' not in data or not data['conteudo']:
            return jsonify({'erro': 'Corpo da requisição deve ser JSON com o campo "conteudo".'}), 400 # Bad Request

        conteudo = data.get('conteudo')

        # Cria uma nova instância do modelo Mensagem
        nova_mensagem = Mensagem(
            negociacao_id=negociacao.id, # Associa a mensagem à negociação
            remetente_id=current_user_id, # Associa a mensagem ao usuário logado como remetente
            conteudo=conteudo # Define o conteúdo da mensagem
        )

        # Adiciona a nova mensagem à sessão do banco de dados e salva
        db.session.add(nova_mensagem)
        db.session.commit()

        # Opcional: Atualizar a data de atualização da negociação
        negociacao.data_atualizacao = datetime.utcnow()
        db.session.commit() # Salva a alteração na negociação


        # Serializa a mensagem criada para a resposta JSON
        mensagem_json = {
            'id': nova_mensagem.id,
            'negociacao_id': nova_mensagem.negociacao_id,
            'remetente_id': nova_mensagem.remetente_id,
            'conteudo': nova_mensagem.conteudo,
            'data_envio': nova_mensagem.data_envio.isoformat() # Formato ISO para data/hora
        }

        # Retorna a mensagem criada como JSON com status 201
        return jsonify(mensagem_json), 201 # Created

    except Exception as e:
        # Em caso de erro, desfaz a transação no banco de dados
        db.session.rollback()
        # Loga o erro no servidor
        print(f"Erro ao enviar mensagem na negociação {negociacao_id}: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao enviar a mensagem.'}), 500 # Internal Server Error

@negociacao.route('/<int:negociacao_id>', methods=['GET'])
@jwt_required() # Protege esta rota, exigindo um JWT válido
def get_negociacao_data(negociacao_id):
    """
    Endpoint para obter dados de uma negociação específica: mensagens, produto principal, dados da negociação.
    Requer autenticação via JWT.
    """
    try:
        # Obtém o ID do usuário logado a partir do JWT
        current_user_id = get_jwt_identity()

        # Busca a negociação pelo ID fornecido na URL
        negociacao = Negociacao.query.get(negociacao_id)
        if negociacao is None:
            return jsonify({'erro': 'Negociação não encontrada.'}), 404 # Not Found

        # Verifica se o usuário logado participa desta negociação (é o solicitante ou o proprietário)
        if current_user_id != negociacao.solicitante_id and current_user_id != negociacao.proprietario_id:
             return jsonify({'erro': 'Você não participa desta negociação.'}), 403 # Forbidden

        # Serializa os dados da negociação para um dicionário
        negociacao_json = {
            'id': negociacao.id,
            'produto_principal_id': negociacao.produto_principal_id,
            'solicitante_id': negociacao.solicitante_id,
            'proprietario_id': negociacao.proprietario_id,
            'tipo': negociacao.tipo,
            'status': negociacao.status.nome if negociacao.status else 'Desconhecido', # Inclui o nome do status
            'data_criacao': negociacao.data_criacao.isoformat(), # Formato ISO para data/hora
            'data_atualizacao': negociacao.data_atualizacao.isoformat(), # Formato ISO para data/hora
            # Inclui os produtos de troca se o tipo for 'Troca'
            'produtos_troca': [{
                'id': p.id,
                'nome': p.nome,
                'preco': str(p.preco), # Converte Decimal para string
                'categoria': p.categoria.nome if p.categoria else 'Sem Categoria'
                # Adicione outros campos relevantes do produto de troca
            } for p in negociacao.produtos_troca] if negociacao.tipo == 'Troca' else []
        }

        # Serializa os dados do produto principal associado à negociação
        produto_principal_json = {
            'id': negociacao.produto_principal.id,
            'nome': negociacao.produto_principal.nome,
            'descricao': negociacao.produto_principal.descricao,
            'preco': str(negociacao.produto_principal.preco), # Converte Decimal para string
            'status': negociacao.produto_principal.status.nome if negociacao.produto_principal.status else 'Desconhecido', # Inclui o nome do status
            'categoria': negociacao.produto_principal.categoria.nome if negociacao.produto_principal.categoria else 'Sem Categoria', # Inclui o nome da categoria
            'cadastrado_por_id': negociacao.produto_principal.usuario_id
            # Adicione outros campos do produto principal
        }

        # Serializa as mensagens da negociação para uma lista de dicionários
        # Ordena as mensagens por data de envio (opcional, mas útil para exibição)
        mensagens_json = [{
            'id': msg.id,
            'negociacao_id': msg.negociacao_id,
            'remetente_id': msg.remetente_id,
            'conteudo': msg.conteudo,
            'data_envio': msg.data_envio.isoformat() # Formato ISO para data/hora
        } for msg in sorted(negociacao.mensagens, key=lambda msg: msg.data_envio)] # Ordena as mensagens por data

        # Retorna todos os dados combinados em um único JSON com status 200
        return jsonify({
            'negociacao': negociacao_json,
            'produto_principal': produto_principal_json,
            'mensagens': mensagens_json
        }), 200 # OK

    except Exception as e:
        # Loga o erro no servidor
        print(f"Erro ao obter dados da negociação {negociacao_id}: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao obter dados da negociação.'}), 500 # Internal Server Error

@negociacao.route('/<int:negociacao_id>/status', methods=['PUT'])
@jwt_required() # Protege esta rota, exigindo um JWT válido
def update_negociacao_status(negociacao_id):
    """
    Endpoint para aceitar ou rejeitar uma negociação.
    Requer autenticação via JWT.
    Espera um corpo de requisição JSON com o campo 'acao': 'aceitar' ou 'rejeitar'.
    Apenas o proprietário do produto principal pode realizar esta ação.
    """
    try:
        # Obtém o ID do usuário logado a partir do JWT
        current_user_id = get_jwt_identity()

        # Busca a negociação pelo ID fornecido na URL
        negociacao = Negociacao.query.get(negociacao_id)
        if negociacao is None:
            return jsonify({'erro': 'Negociação não encontrada.'}), 404 # Not Found

        # Verifica se o usuário logado é o proprietário do produto principal (quem tem permissão para aceitar/rejeitar)
        if current_user_id != negociacao.proprietario_id:
             return jsonify({'erro': 'Você não tem permissão para alterar o status desta negociação.'}), 403 # Forbidden

        # Verifica se a negociação está em um estado que permite aceitar/rejeitar (geralmente 'Pendente')
        status_pendente = StatusNegociacao.query.filter_by(nome='Pendente').first()
        # Verifica se o status 'Pendente' existe antes de comparar
        if status_pendente and negociacao.status_id != status_pendente.id:
             return jsonify({'erro': f'O status atual da negociação ({negociacao.status.nome}) não permite esta ação.'}), 400 # Bad Request


        # Obtém os dados JSON do corpo da requisição
        data = request.get_json()

        # Valida se o campo 'acao' está presente e tem um valor válido
        if not data or 'acao' not in data or data['acao'] not in ['aceitar', 'rejeitar']:
            return jsonify({'erro': 'Corpo da requisição deve ser JSON com o campo "acao": "aceitar" ou "rejeitar".'}), 400 # Bad Request

        acao = data.get('acao')

        # Busca os objetos de status relevantes no banco de dados
        status_aceita = StatusNegociacao.query.filter_by(nome='Aceita').first()
        status_rejeitada = StatusNegociacao.query.filter_by(nome='Rejeitada').first()
        # Status para o produto principal quando a negociação é concluída (ex: 'Encerrado')
        status_concluida_produto = StatusProduto.query.filter_by(nome='Encerrado').first()

        # Verifica se os status necessários foram encontrados no DB
        if status_aceita is None or status_rejeitada is None or status_concluida_produto is None:
             print("Erro: Status 'Aceita', 'Rejeitada' ou 'Encerrado' para negociação/produto não encontrados no DB.")
             return jsonify({'erro': 'Erro interno do servidor: Status de negociação/produto não configurado.'}), 500 # Internal Server Error


        if acao == 'aceitar':
            # Altera o status da negociação para 'Aceita'
            negociacao.status_id = status_aceita.id
            # Opcional: Mudar o status do produto principal para 'Encerrado' ou similar após a aceitação
            if negociacao.produto_principal:
                 negociacao.produto_principal.status_id = status_concluida_produto.id

            mensagem_resposta = 'Negociação aceita com sucesso.'
            status_resposta = 200 # OK

        elif acao == 'rejeitar':
            # Altera o status da negociação para 'Rejeitada'
            negociacao.status_id = status_rejeitada.id
            # Opcional: Mudar o status do produto principal de volta para 'Aberto' se estava 'Em Negociação'
            status_aberto_produto = StatusProduto.query.filter_by(nome='Aberto').first()
            status_em_negociacao_produto = StatusProduto.query.filter_by(nome='Em Negociação').first()
            # Verifica se os status existem antes de usar
            if status_aberto_produto and status_em_negociacao_produto and negociacao.produto_principal and negociacao.produto_principal.status_id == status_em_negociacao_produto.id:
                 negociacao.produto_principal.status_id = status_aberto_produto.id

            mensagem_resposta = 'Negociação rejeitada.'
            status_resposta = 200 # OK

        # Atualiza a data de atualização da negociação
        negociacao.data_atualizacao = datetime.utcnow()
        # Salva as alterações no banco de dados
        db.session.commit()

        # Retorna uma mensagem de sucesso e o novo status da negociação
        return jsonify({'mensagem': mensagem_resposta, 'status_negociacao': negociacao.status.nome}), status_resposta

    except Exception as e:
        # Em caso de erro, desfaz a transação no banco de dados
        db.session.rollback()
        # Loga o erro no servidor
        print(f"Erro ao atualizar status da negociação {negociacao_id}: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao atualizar o status da negociação.'}), 500 # Internal Server Error

@negociacao.route('/<int:negociacao_id>', methods=['DELETE'])
@jwt_required() # Protege esta rota, exigindo um JWT válido
def cancel_negociacao(negociacao_id):
    """
    Endpoint para cancelar uma negociação.
    Requer autenticação via JWT.
    Apenas o solicitante ou o proprietário podem cancelar (dependendo da regra de negócio).
    Vamos permitir que ambos cancelem se o status for 'Pendente' ou 'Aceita'.
    """
    try:
        # Obtém o ID do usuário logado a partir do JWT
        current_user_id = get_jwt_identity()

        # Busca a negociação pelo ID fornecido na URL
        negociacao = Negociacao.query.get(negociacao_id)
        if negociacao is None:
            return jsonify({'erro': 'Negociação não encontrada.'}), 404 # Not Found

        # Verifica se o usuário logado tem permissão para cancelar (é o solicitante OU o proprietário)
        # Ajuste esta lógica de permissão conforme sua regra de negócio
        if current_user_id != negociacao.solicitante_id and current_user_id != negociacao.proprietario_id:
             return jsonify({'erro': 'Você não tem permissão para cancelar esta negociação.'}), 403 # Forbidden

        # Opcional: Permitir cancelamento apenas em certos status da negociação (ex: 'Pendente', 'Aceita')
        status_pendente = StatusNegociacao.query.filter_by(nome='Pendente').first()
        status_aceita = StatusNegociacao.query.filter_by(nome='Aceita').first()
        status_cancelada = StatusNegociacao.query.filter_by(nome='Cancelada').first()

        # Verifica se os status necessários existem antes de usar
        if status_pendente is None or status_aceita is None or status_cancelada is None:
             print("Erro: Status 'Pendente', 'Aceita' ou 'Cancelada' para negociação não encontrados no DB.")
             return jsonify({'erro': 'Erro interno do servidor: Status de negociação não configurado.'}), 500 # Internal Server Error


        # Verifica se o status atual da negociação permite o cancelamento
        if negociacao.status_id not in [status_pendente.id, status_aceita.id]:
             return jsonify({'erro': f'O status atual da negociação ({negociacao.status.nome}) não permite cancelamento.'}), 400 # Bad Request

        # Altera o status da negociação para 'Cancelada'
        negociacao.status_id = status_cancelada.id
        # Opcional: Mudar o status do produto principal de volta para 'Aberto' se estava 'Em Negociação' ou 'Encerrado' (se aceita)
        status_aberto_produto = StatusProduto.query.filter_by(nome='Aberto').first()
        status_em_negociacao_produto = StatusProduto.query.filter_by(nome='Em Negociação').first()
        status_encerrado_produto = StatusProduto.query.filter_by(nome='Encerrado').first()

        # Verifica se os status do produto existem antes de usar
        if status_aberto_produto and negociacao.produto_principal:
             if status_em_negociacao_produto and negociacao.produto_principal.status_id == status_em_negociacao_produto.id:
                 negociacao.produto_principal.status_id = status_aberto_produto.id
             elif status_encerrado_produto and negociacao.produto_principal.status_id == status_encerrado_produto.id:
                  # Se a negociação foi aceita e depois cancelada, o produto pode ter ido para 'Encerrado'
                  # Decide se ele volta para 'Aberto' ou outro status
                  negociacao.produto_principal.status_id = status_aberto_produto.id # Exemplo: volta para Aberto


        # Atualiza a data de atualização da negociação
        negociacao.data_atualizacao = datetime.utcnow()
        # Salva as alterações no banco de dados
        db.session.commit()

        # Retorna uma mensagem de sucesso e o novo status da negociação
        return jsonify({'mensagem': 'Negociação cancelada com sucesso.', 'status_negociacao': negociacao.status.nome}), 200 # OK

    except Exception as e:
        # Em caso de erro, desfaz a transação no banco de dados
        db.session.rollback()
        # Loga o erro no servidor
        print(f"Erro ao cancelar negociação {negociacao_id}: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao cancelar a negociação.'}), 500 # Internal Server Error
