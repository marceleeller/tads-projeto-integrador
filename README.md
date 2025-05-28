# Projeto integrador
Sistema para facilitar a troca e doação de produtos em comunidades de cidades do interior do Tocantins.

## Backend - Projeto de Trocas e Doações

Backend da API para o sistema de trocas e doações.

### Pré-requisitos

* Python 3.8+
* pip
* Git
* MySQL Server

### Configuração Rápida

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/marceleeller/tads-projeto-integrador
    cd tads-projeto-integrador/backend/
    ```

2.  **Crie e Ative o Ambiente Virtual (`venv`):**
    ```bash
    python3 -m venv venv
    venv\Scripts\activate # Windows
    # Para macOS/Linux: source venv/bin/activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo `.env` na pasta `backend/` com o seguinte conteúdo (ajuste conforme necessário):
    ```env
    FLASK_APP=app.py
    FLASK_DEBUG=1
    DATABASE_URL="mysql+pymysql://USUARIO:SENHA@HOST:PORTA/NOME_DO_BANCO"
    # Exemplo: DATABASE_URL="mysql+pymysql://jv:asdfg@127.0.0.1:3306/integrador"
    JWT_SECRET_KEY="SUA_CHAVE_SECRETA_AQUI"
    ```

5.  **Banco de Dados MySQL:**
    * Verifique se o MySQL Server está rodando.
    * Crie o banco de dados e as tabelas utilizando o script SQL fornecido no repositório:
        1. Acesse o MySQL pelo terminal ou por uma ferramenta gráfica (ex: MySQL Workbench).
        2. Execute o script localizado em `/db/ecotroca_db.sql` para criar o banco de dados e todas as tabelas necessárias:
            ```bash
            mysql -u USUARIO -p < db/ecotroca_db.sql
            ```
            Substitua `USUARIO` pelo seu usuário do MySQL.
        3. O script irá criar o banco de dados (ex: `ecotroca`) e todas as tabelas automaticamente.

### Executando a Aplicação

1.  Certifique-se de que o ambiente virtual (`venv`) está ativo.
2.  Execute o servidor Flask:
    ```bash
    flask run
    ```
3.  A API estará disponível em `http://127.0.0.1:5000/`.

## Frontend - Como Executar

O frontend deste projeto é totalmente baseado em arquivos estáticos (HTML, CSS e JavaScript puro), localizados na pasta `frontend/`. Não é necessário instalar dependências ou rodar comandos npm.

> **Observação:** Utilizamos o [Bootstrap](https://getbootstrap.com/) via CDN para facilitar a estilização e responsividade das páginas.

#### Como acessar

1. **Abra o arquivo `index.html`**  
   Navegue até a pasta `frontend/` e abra o arquivo `index.html` em seu navegador de preferência.

2. **Atenção:**  
   - Para que todas as funcionalidades funcionem corretamente (login, cadastro, negociações), o backend precisa estar rodando.
   

#### Estrutura das telas

- `index.html`: Tela de login
- `pages/pagina-inicial.html`: Página principal com listagem de produtos
- `pages/cadastro.html`: Cadastro de usuário
- `pages/cadastro-produto.html`: Cadastro de produto
- `pages/meus-produtos.html`: Gerenciamento dos produtos do usuário
- `pages/negociacao-troca.html` e `pages/negociacao-doacao.html`: Telas de negociação

Os arquivos JavaScript responsáveis pela lógica estão na pasta `js/` e o CSS em `style/style.css`.