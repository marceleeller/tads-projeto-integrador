<p align="center">
  <img alt="GitHub language count" src="https://img.shields.io/github/languages/count/marceleeller/tads-projeto-integrador?color=%2304D361">
  <img alt="Repository size" src="https://img.shields.io/github/repo-size/marceleeller/tads-projeto-integrador">
  <a href="https://github.com/marceleeller/tads-projeto-integrador/commits/main">
    <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/marceleeller/tads-projeto-integrador">
  </a>
</p>

<h1 align="center">
    <img src="./Documentacao/img/banner.png" alt="Banner do Projeto Integrador" />
</h1>

<h4 align="center">
   🌱 Projeto Integrador - Ecotroca 🌱
</h4>

<p align="center">
 <a href="#-sobre-o-projeto">Sobre</a> •
 <a href="#-funcionalidades">Funcionalidades</a> •
 <a href="#-backend">Backend</a> •
 <a href="#-frontend">Frontend</a> •
 <a href="#-como-executar">Como executar</a> •
 <a href="#-tecnologias">Tecnologias</a> •
 <a href="#-contribuidores">Contribuidores</a>
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
# Exemplo: DATABASE_URL="mysql+pymysql://jv:asdfg@127.0.0.1:3306/integrador"
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
Utilizamos o [Bootstrap](https://getbootstrap.com/) via CDN para facilitar a estilização e responsividade das páginas.

#### Como acessar

1. Abra o arquivo `index.html`  
   Navegue até a pasta `frontend/` e abra o arquivo `index.html` em seu navegador de preferência.

2. **Atenção:**  
   - Para que todas as funcionalidades funcionem corretamente (login, cadastro, negociações), o backend precisa estar rodando.
   - Para evitar possíveis problemas de CORS ao acessar diretamente pelo navegador, você pode rodar um servidor HTTP simples:
     ```bash
     # No Windows (PowerShell) dentro da pasta frontend:
     python -m http.server 8080
     ```
     Depois, acesse `http://localhost:8080` no navegador.

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

Abra o arquivo `frontend/index.html` no navegador  
**ou** rode um servidor HTTP local na pasta `frontend` e acesse pelo navegador.

---

## 🛠 Tecnologias

- **Backend:** Python, Flask, MySQL, SQLAlchemy, JWT
- **Frontend:** HTML, CSS, JavaScript, [Bootstrap](https://getbootstrap.com/)

---

## 👨‍💻 Contribuidores

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/marceleeller">
        <img src="https://avatars.githubusercontent.com/u/126519901?v=4" width="100px;" alt="Marcele Eller"/><br>
        <sub><b>Marcele Eller</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/grasieletinoco">
        <img src="https://avatars.githubusercontent.com/u/120054760?v=4" width="100px;" alt="Grasiele Tinoco"/><br>
        <sub><b>Grasiele Tinoco</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/isadeop">
        <img src="https://avatars.githubusercontent.com/u/138228355?v=4" width="100px;" alt="Isadora de Oliveira"/><br>
        <sub><b>Isadora de Oliveira</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/JaquelineAPSantos">
        <img src="https://avatars.githubusercontent.com/u/94487656?v=4" width="100px;" alt="Jaqueline Santos"/><br>
        <sub><b>Jaqueline Santos</b></sub>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center">
      <a href="https://github.com/PAKell">
        <img src="https://avatars.githubusercontent.com/u/131540455?v=4" width="100px;" alt="Kelly Pedroso"/><br>
        <sub><b>Kelly Pedroso</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/ErickFPrado">
        <img src="https://media.licdn.com/dms/image/D4D03AQFDqDhMaqWfaA/profile-displayphoto-shrink_400_400/0/1690839347214?e=1712793600&v=beta&t=wJvSdyVOiZUzSlQIwxZcehQ2gRCBfaxd4Rr3DVRZhrA" width="100px;" alt="Erick Prado"/><br>
        <sub><b>Erick Prado</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/giperuzzo">
        <img src="https://avatars.githubusercontent.com/u/127308320?v=4" width="100px;" alt="Gislene Peruzzo"/><br>
        <sub><b>Gislene Peruzzo</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Antoniobarrosdecastro">
        <img src="https://avatars.githubusercontent.com/u/147821067?v=4" width="100px;" alt="Antonio Barros"/><br>
        <sub><b>Antonio Barros</b></sub>
      </a>
    </td>
  </tr>
</table>