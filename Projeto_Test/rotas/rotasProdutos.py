# routes/product_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

# Importa db e modelos do arquivo models.py
# Certifique-se de que o arquivo models.py está no diretório correto e acessível
from camadaModelo import db, Produto, StatusProduto, Categoria, Usuario, Negociacao # Importa Negociacao para a rota /meus

# Cria um Blueprint para as rotas de produtos
# O prefixo '/produtos' será adicionado a todas as rotas definidas neste Blueprint
produto = Blueprint('product', __name__, url_prefix='/produtos')

# --- Rotas de Produtos ---

@produto.route('/', methods=['GET'])
@jwt_required() # Protege esta rota, exigindo um JWT válido
def get_produtos_ativos():
    """
    Endpoint para obter todos os produtos cadastrados e ativos.
    Produtos ativos são aqueles cujo status NÃO é 'Em Negociação' ou 'Encerrado'.
    Requer autenticação via JWT.
    """
    try:
        # Busca os objetos StatusProduto para 'Em Negociação' e 'Encerrado' pelos seus nomes
        status_em_negociacao = StatusProduto.query.filter_by(nome='Em Negociação').first()
        status_encerrado = StatusProduto.query.filter_by(nome='Encerrado').first()

        # Inicia a consulta para o modelo Produto
        query = Produto.query

        # Filtra os produtos excluindo aqueles com status 'Em Negociação' ou 'Encerrado'
        # Verifica se os objetos de status foram encontrados antes de usar seus IDs
        if status_em_negociacao:
             query = query.filter(Produto.status_id != status_em_negociacao.id)

        if status_encerrado:
             query = query.filter(Produto.status_id != status_encerrado.id)

        # Executa a consulta e obtém todos os produtos ativos
        produtos_ativos = query.all()

        # Opcional: Aviso se os status de exclusão não foram encontrados (pode indicar um problema de inicialização do DB)
        if not status_em_negociacao and not status_encerrado:
             print("Aviso: Status 'Em Negociação' ou 'Encerrado' não encontrados. Retornando todos os produtos.")

        # Serializa a lista de objetos Produto para uma lista de dicionários para a resposta JSON
        lista_produtos_json = []
        for produto in produtos_ativos:
            lista_produtos_json.append({
                'id': produto.id,
                'nome': produto.nome,
                'descricao': produto.descricao,
                'preco': str(produto.preco), # Converte o tipo Decimal para string para serialização JSON
                'status': produto.status.nome if produto.status else 'Desconhecido', # Inclui o nome do status (se o relacionamento estiver carregado)
                'categoria': produto.categoria.nome if produto.categoria else 'Sem Categoria', # Inclui o nome da categoria (se o relacionamento estiver carregado)
                'cadastrado_por_id': produto.usuario_id # Inclui o ID do usuário que cadastrou o produto
                # Adicione outros campos do produto conforme necessário no JSON de resposta
            })

        # Retorna a lista de produtos ativos como JSON com status 200
        return jsonify(lista_produtos_json), 200 # OK

    except Exception as e:
        # Loga o erro no servidor
        print(f"Erro ao obter produtos ativos: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao obter os produtos.'}), 500 # Internal Server Error

@produto.route('/meus', methods=['GET']) # Rota específica para produtos relacionados ao usuário logado
@jwt_required() # Protege esta rota, exigindo um JWT válido
def get_meus_produtos():
    """
    Endpoint para obter todos os produtos cadastrados pelo usuário logado
    OU que estejam envolvidos em negociações (seja como solicitante ou proprietário do produto principal).
    Requer autenticação via JWT.
    """
    try:
        # Obtém o ID do usuário logado a partir do JWT
        current_user_id = get_jwt_identity()

        # 1. Busca produtos cadastrados diretamente pelo usuário logado
        produtos_cadastrados = Produto.query.filter_by(usuario_id=current_user_id).all()

        # 2. Busca negociações onde o usuário é o solicitante e obtém os produtos principais dessas negociações
        # Importa Negociacao aqui para evitar circular import se Negociacao importar Produto em models.py
        # from models import Negociacao # Já importado no início do arquivo
        negociacoes_solicitadas = Negociacao.query.filter_by(solicitante_id=current_user_id).all()
        produtos_solicitados = [neg.produto_principal for neg in negociacoes_solicitadas if neg.produto_principal] # Garante que o produto principal existe

        # 3. Busca negociações onde o usuário é o proprietário do produto principal e obtém esses produtos
        negociacoes_recebidas = Negociacao.query.filter_by(proprietario_id=current_user_id).all()
        produtos_recebidos_negociacao = [neg.produto_principal for neg in negociacoes_recebidas if neg.produto_principal] # Garante que o produto principal existe


        # Combina as três listas de produtos e remove duplicatas usando um dicionário
        # A chave do dicionário é o ID do produto, garantindo unicidade
        todos_produtos_relacionados_dict = {produto.id: produto for produto in produtos_cadastrados + produtos_solicitados + produtos_recebidos_negociacao}
        # Converte os valores do dicionário de volta para uma lista de objetos Produto
        todos_produtos_relacionados = list(todos_produtos_relacionados_dict.values())


        # Serializa a lista de objetos Produto para uma lista de dicionários para a resposta JSON
        lista_produtos_json = []
        for produto in todos_produtos_relacionados:
            lista_produtos_json.append({
                'id': produto.id,
                'nome': produto.nome,
                'descricao': produto.descricao,
                'preco': str(produto.preco), # Converte Decimal para string para JSON
                'status': produto.status.nome if produto.status else 'Desconhecido', # Inclui o nome do status
                'categoria': produto.categoria.nome if produto.categoria else 'Sem Categoria', # Inclui o nome da categoria
                'cadastrado_por_id': produto.usuario_id # Inclui o ID do usuário que cadastrou
                # Adicione outros campos do produto conforme necessário
            })

        # Retorna a lista de produtos relacionados ao usuário como JSON com status 200
        return jsonify(lista_produtos_json), 200 # OK

    except Exception as e:
        # Loga o erro no servidor
        print(f"Erro ao obter produtos do usuário: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao obter os produtos do usuário.'}), 500 # Internal Server Error

@produto.route('/<int:produto_id>', methods=['GET']) # Rota para obter um produto específico por ID
@jwt_required() # Protege esta rota, exigindo um JWT válido
def get_produto_por_id(produto_id):
    """
    Endpoint para obter um produto específico pelo seu ID.
    Requer autenticação via JWT.
    """
    try:
        # Busca o produto no banco de dados pelo ID fornecido na URL
        produto = Produto.query.get(produto_id)

        # Verifica se o produto foi encontrado
        if produto is None:
            return jsonify({'erro': 'Produto não encontrado.'}), 404 # Not Found

        # Serializa o objeto Produto para um dicionário para a resposta JSON
        produto_json = {
            'id': produto.id,
            'nome': produto.nome,
            'descricao': produto.descricao,
            'preco': str(produto.preco), # Converte Decimal para string para JSON
            'status': produto.status.nome if produto.status else 'Desconhecido', # Inclui o nome do status
            'categoria': produto.categoria.nome if produto.categoria else 'Sem Categoria', # Inclui o nome da categoria
            'cadastrado_por_id': produto.usuario_id # Inclui o ID do usuário que cadastrou
            # Adicione outros campos do produto conforme necessário
        }

        # Retorna o produto como JSON com status 200
        return jsonify(produto_json), 200 # OK

    except Exception as e:
        # Loga o erro no servidor
        print(f"Erro ao obter produto por ID {produto_id}: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao obter o produto.'}), 500 # Internal Server Error

@produto.route('/<int:produto_id>', methods=['PUT']) # Rota para alterar um produto específico por ID
@jwt_required() # Protege esta rota, exigindo um JWT válido
def update_produto(produto_id):
    """
    Endpoint para alterar um produto específico pelo seu ID.
    Requer autenticação via JWT.
    Espera um corpo de requisição JSON com os dados a serem alterados.
    """
    try:
        # Obtém o ID do usuário logado a partir do JWT
        current_user_id = get_jwt_identity()

        # Busca o produto no banco de dados pelo ID fornecido na URL
        produto = Produto.query.get(produto_id)

        # Verifica se o produto foi encontrado
        if produto is None:
            return jsonify({'erro': 'Produto não encontrado.'}), 404 # Not Found

        # Opcional: Verificar se o usuário logado é o proprietário do produto antes de permitir a alteração
        # Se você quiser que apenas o usuário que cadastrou possa alterar o produto, descomente o código abaixo.
        if produto.usuario_id != current_user_id:
             return jsonify({'erro': 'Você não tem permissão para alterar este produto.'}), 403 # Forbidden


        # Obtém os dados JSON do corpo da requisição
        data = request.get_json()

        # Valida se o corpo da requisição é JSON e não está vazio
        if not data:
             return jsonify({'erro': 'Corpo da requisição deve ser JSON com dados para alteração.'}), 400 # Bad Request


        # Atualiza os campos do produto com base nos dados recebidos no JSON
        # Itera sobre os pares chave-valor no dicionário JSON recebido
        for campo, valor in data.items():
            # Verifica se o campo recebido existe no modelo Produto e não é um campo que não deve ser alterado via PUT (ID, usuario_id)
            if hasattr(produto, campo) and campo not in ['id', 'usuario_id']:
                # Tratar a atualização do status separadamente se o valor for o nome do status
                if campo == 'status' and isinstance(valor, str):
                    status_obj = StatusProduto.query.filter_by(nome=valor).first()
                    if status_obj:
                        produto.status_id = status_obj.id
                    else:
                        return jsonify({'erro': f'Status "{valor}" inválido.'}), 400 # Bad Request
                # Tratar a atualização da categoria separadamente se o valor for o nome da categoria
                elif campo == 'categoria' and isinstance(valor, str):
                     categoria_obj = Categoria.query.filter_by(nome=valor).first()
                     if categoria_obj:
                         produto.categoria_id = categoria_obj.id
                     else:
                         return jsonify({'erro': f'Categoria "{valor}" inválida.'}), 400 # Bad Request
                else:
                    # Se não for status ou categoria (pelo nome), atualiza o atributo diretamente
                    setattr(produto, campo, valor)
            # Opcional: Adicionar validação específica para outros campos (ex: garantir que 'preco' é numérico)


        # Salva as alterações no banco de dados
        db.session.commit()

        # Serializa o objeto Produto atualizado para um dicionário para a resposta JSON
        produto_json = {
            'id': produto.id,
            'nome': produto.nome,
            'descricao': produto.descricao,
            'preco': str(produto.preco), # Converte Decimal para string para JSON
            'status': produto.status.nome if produto.status else 'Desconhecido', # Inclui o nome do status
            'categoria': produto.categoria.nome if produto.categoria else 'Sem Categoria', # Inclui o nome da categoria
            'cadastrado_por_id': produto.usuario_id # Inclui o ID do usuário que cadastrou
            # Adicione outros campos do produto conforme necessário
        }

        # Retorna o produto atualizado como JSON com status 200
        return jsonify(produto_json), 200 # OK

    except Exception as e:
        # Em caso de erro no banco de dados, desfaz a transação
        db.session.rollback()
        # Loga o erro no servidor
        print(f"Erro ao alterar produto por ID {produto_id}: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao alterar o produto.'}), 500 # Internal Server Error

@produto.route('/<int:produto_id>', methods=['DELETE']) # Rota para deletar um produto específico por ID
@jwt_required() # Protege esta rota, exigindo um JWT válido
def delete_produto(produto_id):
    """
    Endpoint para deletar um produto específico pelo seu ID.
    Requer autenticação via JWT.
    """
    try:
        # Obtém o ID do usuário logado a partir do JWT
        current_user_id = get_jwt_identity()

        # Busca o produto no banco de dados pelo ID fornecido na URL
        produto = Produto.query.get(produto_id)

        # Verifica se o produto foi encontrado
        if produto is None:
            return jsonify({'erro': 'Produto não encontrado.'}), 404 # Not Found

        # Opcional: Verificar se o usuário logado é o proprietário do produto antes de permitir a exclusão
        # Se você quiser que apenas o usuário que cadastrou possa deletar o produto, descomente o código abaixo.
        if produto.usuario_id != current_user_id:
             return jsonify({'erro': 'Você não tem permissão para deletar este produto.'}), 403 # Forbidden

        # Antes de deletar o produto, você pode precisar lidar com relacionamentos (Negociações, Mensagens)
        # Dependendo da sua regra de negócio e da configuração de cascade no DB, você pode querer:
        # 1. Impedir a exclusão se houver negociações ativas envolvendo este produto.
        # 2. Deletar negociações e mensagens associadas (como feito no exemplo abaixo).
        # 3. Definir FKs como NULL (se aplicável).

        # Importa Negociacao e Mensagem aqui para evitar circular import se necessário
        from camadaModelo import Negociacao, Mensagem
        # Exemplo: Deletar negociações onde este produto é o produto principal
        negociacoes_principais = Negociacao.query.filter_by(produto_principal_id=produto.id).all()
        for neg in negociacoes_principais:
            # Deletar mensagens associadas a essas negociações antes de deletar a negociação
            Mensagem.query.filter_by(negociacao_id=neg.id).delete()
            # Remover associações na tabela many-to-many se necessário (SQLAlchemy com cascade pode lidar com isso)
            # neg.produtos_troca = [] # Exemplo: limpar a associação se necessário
            db.session.delete(neg)

        # Exemplo: Deletar associações na tabela many-to-many onde este produto é um produto de troca
        # SQLAlchemy com cascade='all, delete-orphan' no relacionamento produtos_troca em Negociacao pode lidar com isso automaticamente.
        # Caso contrário, pode precisar de lógica manual ou query direta na tabela de associação.
        # Exemplo: db.session.query(negociacao_produtos_troca).filter_by(produto_id=produto.id).delete()


        # Remove o produto do banco de dados
        db.session.delete(produto)
        # Salva as alterações no banco de dados
        db.session.commit()

        # Retorna uma resposta de sucesso
        # Status 200 OK com mensagem ou 204 No Content (sem corpo na resposta) são comuns para DELETE
        return jsonify({'mensagem': 'Produto deletado com sucesso.'}), 200 # OK

    except Exception as e:
        # Em caso de erro no banco de dados, desfaz a transação
        db.session.rollback()
        # Loga o erro no servidor
        print(f"Erro ao deletar produto por ID {produto_id}: {e}")
        # Retorna um erro interno do servidor
        return jsonify({'erro': 'Ocorreu um erro interno ao deletar o produto.'}), 500 # Internal Server Error
