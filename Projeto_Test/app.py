# app.py
import os
from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import timedelta
import logging # Importa o módulo de logging

# Importa db e modelos do models.py
# Certifique-se de que o arquivo models.py está no mesmo diretório
from camadaModelo import db, Disponibilidade, StatusSolicitacao, Categoria # Importa modelos para inicialização inicial do DB

# Importa os Blueprints das rotas
# Certifique-se de que a pasta 'rotas' existe e contém os arquivos de rotas
from rotas.rotasAutenticacao import autenticacao
from rotas.rotasProdutos import produto
from rotas.rotasNegociacao import negociacao

# Configuração básica de logging
# Configura o formato e o nível das mensagens de log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Configuração de logging inicializada.")


# --- Função Factory para criar a aplicação Flask ---
# Esta é uma prática recomendada para aplicações Flask maiores
def create_app():
    # Cria a instância da aplicação Flask
    app = Flask(__name__)

    # --- Configurações da Aplicação Flask ---
    # Define a chave secreta para segurança da aplicação (sessões, etc.)
    # Use variáveis de ambiente em produção para segurança!
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sua_chave_secreta_padrao_PARA_PRODUCAO_USE_ENV')

    # Configurações do banco de dados MySQL
    # Obtém as credenciais do banco de dados de variáveis de ambiente ou usa valores padrão
    # Use variáveis de ambiente em produção para segurança!
    DB_USER = os.environ.get('DB_USER', 'seu_usuario_mysql')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'sua_senha_mysql')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', 3306)
    DB_NAME = os.environ.get('DB_NAME', 'seu_banco_de_dados')

    # Constrói a string de conexão do banco de dados SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    # Desabilita o rastreamento de modificações do SQLAlchemy para economizar recursos
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configurações do Flask-JWT-Extended
    # Define a chave secreta para assinar os JWTs (deve ser diferente da SECRET_KEY principal)
    # Use variáveis de ambiente em produção para segurança!
    app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY', 'sua_chave_secreta_jwt_PADRAO_MUDE_ISSO')
    # Define o tempo de expiração dos tokens de acesso (exemplo: 1 hora)
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    # --- Inicializa as Extensões ---
    # Associa o objeto 'db' (inicializado em models.py) à instância do Flask app
    db.init_app(app)
    # Inicializa o Flask-JWT-Extended associando-o à instância do Flask app
    jwt = JWTManager(app)

    # --- Registra os Blueprints das Rotas ---
    # Registra cada Blueprint na aplicação Flask principal
    app.register_blueprint(autenticacao) # Rotas de autenticação (ex: /auth/login, /auth/registrar)
    app.register_blueprint(produto) # Rotas de produtos (ex: /produtos, /produtos/meus)
    app.register_blueprint(negociacao) # Rotas de negociação (ex: /negociacoes, /negociacoes/<id>/mensagens)

    # Opcional: Configurar callbacks do JWTManager aqui, se necessário
    # Por exemplo, um callback para carregar o objeto usuário a partir da identidade no token
    # @jwt.user_lookup_loader
    # def user_lookup_callback(_jwt_header, jwt_data):
    #     identity = jwt_data["sub"] # "sub" é a chave padrão para a identidade no JWT
    #     from models import Usuario # Importa Usuario aqui para evitar circular import
    #     return Usuario.query.get(identity) # Retorna o objeto Usuario ou None

    # Retorna a instância da aplicação Flask criada e configurada
    return app

# --- Execução da Aplicação ---
# Este bloco garante que o servidor só inicie se o script for executado diretamente
if __name__ == '__main__':
    # Cria a instância da aplicação usando a função factory
    app = create_app()

    # Entra no contexto da aplicação para poder interagir com o SQLAlchemy
    with app.app_context():
        try:
            # Cria as tabelas do banco de dados se elas não existirem.
            # ATENÇÃO: Em produção, use ferramentas de migrations (ex: Flask-Migrate)
            # em vez de db.create_all() para gerenciar alterações no esquema do DB.
            db.create_all()
            logging.info("Banco de dados conectado e tabelas verificadas/criadas.")

            # Opcional: Adicionar status e categorias iniciais ao banco de dados se não existirem
            # Isso é crucial para que as rotas que dependem desses status/categorias funcionem corretamente.
            # Verifica se os status de Produto existem e os adiciona se não
            if not Disponibilidade.query.first():
                 db.session.add(Disponibilidade(nome='DISPONIVEL'))
                 db.session.add(Disponibilidade(nome='EM NEGOCIAÇÃO'))
                 db.session.add(Disponibilidade(nome='NEGOCIAÇÃO ENCERRADA'))
                 db.session.commit()
                 logging.info("Status iniciais de Produto adicionados.")
            else:
                 logging.info("Status iniciais de Produto já existem.")


            # Verifica se os status de Negociação existem e os adiciona se não
            if not StatusSolicitacao.query.first():
                 db.session.add(StatusSolicitacao(nome='PENDENTE'))
                 db.session.add(StatusSolicitacao(nome='APROVADA'))
                 db.session.add(StatusSolicitacao(nome='REJEITADA'))
                 db.session.add(StatusSolicitacao(nome='REJEITADA'))
                 db.session.add(StatusSolicitacao(nome='APROVADA'))
                 db.session.commit()
                 logging.info("Status iniciais de Negociação adicionados.")
            else:
                 logging.info("Status iniciais de Negociação já existem.")


            # Verifica se as categorias existem e as adiciona se não
            if not Categoria.query.first():
                 db.session.add(Categoria(nome='Eletrônicos'))
                 db.session.add(Categoria(nome='Livros'))
                 db.session.add(Categoria(nome='Móveis'))
                 db.session.commit()
                 logging.info("Categorias iniciais adicionadas.")
            else:
                 logging.info("Categorias iniciais já existem.")


        except Exception as e:
            # Loga um erro fatal se a conexão ou criação de tabelas falhar
            logging.error(f"Erro fatal ao conectar ou criar tabelas do MySQL: {e}")

    logging.info("Iniciando o servidor Flask...")
    # Inicia o servidor de desenvolvimento Flask
    # debug=True habilita o modo debug (recarregamento automático, traceback de erros) - Use SOMENTE em desenvolvimento!
    # host='0.0.0.0' torna o servidor acessível externamente (útil em ambientes como Docker ou redes locais)
    # port=5000 define a porta em que o servidor irá rodar (ajuste se necessário)
    app.run(debug=True, host='0.0.0.0', port=5000)
