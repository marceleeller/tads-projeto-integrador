# tads-projeto-integrador
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
    * Crie o banco de dados (ex: `integrador`) no MySQL se ele não existir:
        ```sql
        CREATE DATABASE IF NOT EXISTS integrador;
        ```
    * **Para criar as tabelas:** Descomente a linha `create_tables()` no final do arquivo `app.py`, rode a aplicação uma vez (próximo passo), e depois comente a linha novamente.

### Executando a Aplicação

1.  Certifique-se de que o ambiente virtual (`venv`) está ativo.
2.  Execute o servidor Flask:
    ```bash
    flask run
    ```
3.  A API estará disponível em `http://127.0.0.1:5000/`.

---