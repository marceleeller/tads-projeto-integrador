<p align="center">
  <img alt="GitHub language count" src="https://img.shields.io/github/languages/count/marceleeller/tads-projeto-integrador?color=%2304D361">
  <img alt="Repository size" src="https://img.shields.io/github/repo-size/marceleeller/tads-projeto-integrador">
  <a href="https://github.com/marceleeller/tads-projeto-integrador/commits/main">
    <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/marceleeller/tads-projeto-integrador">
  </a>
</p>


<h4 align="center">
   🌱 Projeto Integrador - Ecotroca 🌱
</h4>

<p align="center">
 <a href="#-sobre-o-projeto">Sobre</a> •
 <a href="#-funcionalidades">Funcionalidades</a> •
 <a href="#-backend">Backend</a> •
 <a href="#-frontend">Frontend</a> •
 <a href="#-como-executar">Como executar</a> •
 <a href="#-tecnologias">Tecnologias</a>
</p>

---

## 💻 Sobre o projeto

🌱 **Ecotroca** é um sistema para facilitar a troca e doação de produtos em comunidades de cidades do interior do Tocantins. O objetivo é promover o consumo consciente e fortalecer laços comunitários.

---

## ⚙️ Funcionalidades

- Cadastro e login de usuários
- Cadastro, edição e exclusão de produtos
- Listagem de produtos disponíveis para troca ou doação
- Filtros de busca por categoria, tipo e status
- Iniciar e gerenciar negociações (troca ou doação)
- Chat entre usuários durante negociações
- Histórico de negociações

---

## 🖥️ Backend

### Pré-requisitos

- Python 3.8+
- pip
- Git
- MySQL Server

### Configuração Rápida

```bash
# Clone o repositório
git clone https://github.com/marceleeller/tads-projeto-integrador
cd tads-projeto-integrador/backend/
```

```bash
# Crie e ative o ambiente virtual
python3 -m venv venv
venv\Scripts\activate  # Windows
# Para macOS/Linux: source venv/bin/activate
```

```bash
# Instale as dependências
pip install -r requirements.txt
```

```bash
# Crie o arquivo .env na pasta backend/ com o seguinte conteúdo:
FLASK_APP=app.py
FLASK_DEBUG=1
DATABASE_URL="mysql+pymysql://USUARIO:SENHA@HOST:PORTA/NOME_DO_BANCO"
# Exemplo: DATABASE_URL="mysql+pymysql://jv:asdfg@127.0.0.1:3306/ecotroca"
JWT_SECRET_KEY="SUA_CHAVE_SECRETA_AQUI"
```

#### Banco de Dados

- Certifique-se de que o MySQL Server está rodando.
- Execute o script localizado em `/db/ecotroca_db.sql` para criar o banco de dados e todas as tabelas necessárias:
  ```bash
  mysql -u USUARIO -p < db/ecotroca_db.sql
  ```
  Substitua `USUARIO` pelo seu usuário do MySQL.

---

## 🌐 Frontend

O frontend é totalmente baseado em arquivos estáticos (HTML, CSS e JavaScript puro), localizado na pasta `frontend/`.  
Utilizamos o Bootstrap via CDN para facilitar a estilização e responsividade das páginas.

#### Como acessar

1. Abra o arquivo `index.html`  
   Navegue até a pasta `frontend/` e abra o arquivo `index.html` em seu navegador de preferência.

2. **Atenção:**  
   - Para que todas as funcionalidades funcionem corretamente (login, cadastro, negociações), o backend precisa estar rodando.

#### Estrutura das telas

- `index.html`: Tela de login
- `pages/pagina-inicial.html`: Página principal com listagem e filtros de produtos
- `pages/cadastro.html`: Cadastro de novo usuário
- `pages/cadastro-produto.html`: Cadastro e edição de produtos
- `pages/meus-produtos.html`: Gerenciamento dos produtos do usuário
- `pages/minhas-negociacoes.html`: Listagem e gerenciamento das negociações do usuário
- `pages/negociacao-troca.html`: Detalhes, chat e ações de uma negociação de troca
- `pages/negociacao-doacao.html`: Detalhes, chat e ações de uma negociação de doação

Os arquivos JavaScript responsáveis pela lógica estão na pasta `js/` e o CSS em `style/style.css`.

---

## 🚀 Como executar

### Backend

```bash
# Ative o ambiente virtual
venv\Scripts\activate  # Windows
# Para macOS/Linux: source venv/bin/activate

# Execute o servidor Flask
flask run
```
A API estará disponível em `http://127.0.0.1:5000/`.

### Frontend

Abra o arquivo `frontend/index.html` no navegador.

---

## 🛠 Tecnologias

- **Backend:** Python, Flask, MySQL, SQLAlchemy, JWT
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
