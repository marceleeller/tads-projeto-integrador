// Função para obter os parâmetros da URL
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        id: params.get('id')
    };
}

let produtosUsuario = [];
let produtosOfertadosIds = []; // Agora é um array

document.addEventListener('DOMContentLoaded', async () => {
    const { id } = getQueryParams();
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('id_usuario');
    if (!id || !token) {
        alert('Acesso inválido.');
        window.location.href = 'pagina-inicial.html';
        return;
    }

    const nomeUsuario = localStorage.getItem('nome_usuario');
    if (nomeUsuario) {
        const spanBemVindo = document.getElementById('bem-vindo-usuario');
        if (spanBemVindo) {
            spanBemVindo.textContent = `Bem-vindo(a), ${nomeUsuario}`;
        }
    }
    // Carrega dados da negociação (igual doação)
    let data;
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/negociacao/${id}`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!response.ok) {
            alert('Erro ao carregar negociação.');
            window.location.href = 'pagina-inicial.html';
            return;
        }
        data = await response.json();
        console.log(data);
    } catch (error) {
        alert('Erro ao conectar ao servidor.');
        window.location.href = 'pagina-inicial.html';
        return;
    }

    // Preencher dados do produto
    const produto = data.solicitacao.produto_desejado;
    document.getElementById('product-name').textContent = produto.nome_produto;
    document.getElementById('product-description').textContent = produto.descricao;
    document.getElementById('product-category').textContent = produto.categoria?.nome_categoria || '';
    if (produto.imagens && produto.imagens.length > 0) {
        document.getElementById('product-image').src = `${CONFIG.API_BASE_URL.replace('/api', '')}/${produto.imagens[0].url_imagem}`;
    } else {
        document.getElementById('product-image').src = '../assets/placeholder.png';
    }

    // Preencher endereço do produto
    const endereco = produto.endereco;
    const enderecoDiv = document.getElementById('product-address');
    if (endereco && enderecoDiv) {
        enderecoDiv.innerHTML = `
            <strong>Endereço do produto:</strong><br>
            ${endereco.rua}, ${endereco.numero}${endereco.complemento ? ' - ' + endereco.complemento : ''}<br>
            ${endereco.bairro} - ${endereco.cidade}/${endereco.estado}<br>
            CEP: ${endereco.cep}
        `;
    }

    // Preencher mensagens do chat (igual doação)
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
    data.mensagens.forEach(msg => {
        const div = document.createElement('div');
        if (String(msg.id_usuario) === String(userId)) {
            div.className = 'text-end mb-2';
            div.innerHTML = `<span class="badge bg-primary">Você:</span> <span>${msg.conteudo_mensagem}</span>`;
        } else {
            const nomeRemetente = msg.nome_remetente || msg.nome_usuario || "Outro usuário";
            div.className = 'text-start mb-2';
            div.innerHTML = `<span class="badge bg-secondary">${nomeRemetente}:</span> <span>${msg.conteudo_mensagem}</span>`;
        }
        chatMessages.appendChild(div);
    });
    chatMessages.scrollTop = chatMessages.scrollHeight;

    window.idSolicitacaoAtual = data.solicitacao.id_solicitacao;

    const isDono = String(produto.id_usuario) === String(userId);

    // Exibe o box de adicionar produtos só para quem NÃO é dono
    const addProductsBox = document.getElementById('add-products-interface');
    const tradeBox = document.getElementById('my-trade-box');

    // Se solicitação NÃO está em PROCESSANDO, mostra produtos já adicionados e oculta box de adicionar
    if (data.solicitacao.status !== 'PROCESSANDO') {
        addProductsBox.style.display = 'none';
        tradeBox.innerHTML = '';
        (data.solicitacao.produtos_ofertados_details || []).forEach(produto => {
            const col = document.createElement('div');
            col.classList.add('col-md-4');

            const card = document.createElement('div');
            card.classList.add('card', 'shadow');

            const img = document.createElement('img');
            img.src = (produto.imagens && produto.imagens.length > 0)
                ? `${CONFIG.API_BASE_URL.replace('/api', '')}/${produto.imagens[0].url_imagem}`
                : '../assets/placeholder.png';
            img.alt = produto.nome_produto;
            img.classList.add('card-img-top', 'img-fluid');
            img.style.height = '150px';
            img.style.objectFit = 'cover';

            const cardBody = document.createElement('div');
            cardBody.classList.add('card-body', 'text-center');

            const title = document.createElement('h6');
            title.classList.add('card-title');
            title.textContent = produto.nome_produto;

            const description = document.createElement('p');
            description.classList.add('card-text', 'text-muted');
            description.textContent = produto.descricao;

            cardBody.appendChild(title);
            cardBody.appendChild(description);
            card.appendChild(img);
            card.appendChild(cardBody);
            col.appendChild(card);

            tradeBox.appendChild(col);
        });
    } else {
        // Só exibe para quem NÃO é dono do produto
        if (!isDono) {
            addProductsBox.style.display = 'block';
            await carregarProdutosUsuario(token, userId);
            renderizarProdutosParaTroca();
        } else {
            addProductsBox.style.display = 'none';
        }
    }

    // Botões de ação (igual doação, mas para troca)
    const btnContainer = document.querySelector('.text-center.mt-3');
    btnContainer.innerHTML = '';

    if (data.solicitacao.status === 'APROVADA') {
        btnContainer.innerHTML = `
            <div class="alert alert-success text-center fw-bold mb-0">
                Negociação aprovada
            </div>
        `;
    } else if (String(produto.id_usuario) === String(userId)) {
        // Dono do produto: aceitar/recusar
        const btnGroup = document.createElement('div');
        btnGroup.className = 'text-center mt-3 d-flex flex-row justify-content-center flex-column align-items-center gap-2';

        const btnAceitar = document.createElement('button');
        btnAceitar.className = 'btn btn-success w-50';
        btnAceitar.textContent = 'Aceitar troca';
        btnAceitar.onclick = async function () {
            await acaoSolicitacao(window.idSolicitacaoAtual, 'APROVADA');
        };

        const btnRecusar = document.createElement('button');
        btnRecusar.className = 'btn btn-danger w-50';
        btnRecusar.textContent = 'Recusar troca';
        btnRecusar.onclick = async function () {
            await acaoSolicitacao(window.idSolicitacaoAtual, 'RECUSADA');
        };

        btnGroup.appendChild(btnAceitar);
        btnGroup.appendChild(btnRecusar);
        btnContainer.appendChild(btnGroup);
    } else {
        // Não é dono: solicitar troca
        const btnGroup = document.createElement('div');
        btnGroup.className = 'text-center mt-3 d-flex flex-row justify-content-center flex-column align-items-center gap-2';

        const solicitarBtn = document.createElement('button');
        solicitarBtn.className = 'btn btn-success w-50';
        solicitarBtn.id = 'solicitar-btn';
        if (data.solicitacao.status === 'PENDENTE') {
            solicitarBtn.textContent = 'Solicitação pendente';
            solicitarBtn.disabled = true;
        } else {
            solicitarBtn.textContent = 'Solicitar troca';
            solicitarBtn.disabled = false;
            solicitarBtn.onclick = finalizeTrade;
        }
        btnGroup.appendChild(solicitarBtn);

        // Botão cancelar se pendente
        if (data.solicitacao.status === 'PENDENTE') {
            const cancelarBtn = document.createElement('button');
            cancelarBtn.className = 'btn btn-danger mt-2 w-50';
            cancelarBtn.textContent = 'Cancelar solicitação';
            cancelarBtn.onclick = cancelarSolicitacao;
            btnGroup.appendChild(cancelarBtn);
        }

        btnContainer.appendChild(btnGroup);
    }
});

// Carrega os produtos do usuário logado
async function carregarProdutosUsuario(token, userId) {
    try {
        const resp = await fetch(`${CONFIG.API_BASE_URL}/produtos/usuario`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        const produtos = await resp.json();
        // Filtra produtos do usuário logado e DISPONÍVEIS para troca
        produtosUsuario = produtos.filter(p => {
            if (String(p.id_usuario) !== String(userId)) return false;
            // Se não tem solicitações, está disponível
            if (!p.solicitacoes || p.solicitacoes.length === 0) return true;
            // Se TODAS as solicitações NÃO são PENDENTE nem APROVADA, está disponível
            return p.solicitacoes.every(s =>
                s.status !== 'PENDENTE' && s.status !== 'APROVADA'
            );
        });
    } catch (e) {
        produtosUsuario = [];
    }
}

// Renderiza os produtos do usuário para adicionar à troca
function renderizarProdutosParaTroca() {
    const container = document.querySelector('#add-products-interface .d-flex.flex-wrap');
    container.innerHTML = '';
    produtosUsuario.forEach(produto => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.width = '8rem';

        const img = document.createElement('img');
        img.src = (produto.imagens && produto.imagens.length > 0)
            ? `${CONFIG.API_BASE_URL.replace('/api', '')}/${produto.imagens[0].url_imagem}`
            : '../assets/placeholder.png';
        img.className = 'card-img-top';
        img.alt = produto.nome_produto;

        const cardBody = document.createElement('div');
        cardBody.className = 'card-body text-center';

        const title = document.createElement('h6');
        title.className = 'card-title';
        title.textContent = produto.nome_produto;

        const btn = document.createElement('button');
        btn.className = 'btn btn-sm btn-primary';
        btn.textContent = 'Adicionar';
        btn.onclick = () => addToMyTradeBox(produto);

        cardBody.appendChild(title);
        cardBody.appendChild(btn);
        card.appendChild(img);
        card.appendChild(cardBody);
        container.appendChild(card);
    });
}

// Adiciona produto à caixinha de troca (permite vários)
function addToMyTradeBox(produto) {
    if (produtosOfertadosIds.includes(produto.id_produto)) return; // Evita duplicidade

    produtosOfertadosIds.push(produto.id_produto);

    const tradeBox = document.getElementById('my-trade-box');

    const col = document.createElement('div');
    col.classList.add('col-md-4');
    col.dataset.produtoId = produto.id_produto;

    const card = document.createElement('div');
    card.classList.add('card', 'shadow');

    const img = document.createElement('img');
    img.src = (produto.imagens && produto.imagens.length > 0)
        ? `${CONFIG.API_BASE_URL.replace('/api', '')}/${produto.imagens[0].url_imagem}`
        : '../assets/placeholder.png';
    img.alt = produto.nome_produto;
    img.classList.add('card-img-top', 'img-fluid');
    img.style.height = '150px';
    img.style.objectFit = 'cover';

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body', 'text-center');

    const title = document.createElement('h6');
    title.classList.add('card-title');
    title.textContent = produto.nome_produto;

    const description = document.createElement('p');
    description.classList.add('card-text', 'text-muted');
    description.textContent = produto.descricao;

    const removeButton = document.createElement('button');
    removeButton.classList.add('btn', 'btn-sm', 'btn-danger', 'mt-2');
    removeButton.textContent = 'Remover';
    removeButton.onclick = () => {
        col.remove();
        produtosOfertadosIds = produtosOfertadosIds.filter(id => id !== produto.id_produto);
    };

    cardBody.appendChild(title);
    cardBody.appendChild(description);
    cardBody.appendChild(removeButton);
    card.appendChild(img);
    card.appendChild(cardBody);
    col.appendChild(card);

    tradeBox.appendChild(col);
}

// Função para finalizar a troca (enviar solicitação)
async function finalizeTrade() {
    const token = localStorage.getItem('access_token');
    const { id } = getQueryParams();
    if (!produtosOfertadosIds.length) {
        alert('Selecione ao menos um produto para ofertar na troca.');
        return;
    }
    try {
        const resp = await fetch(`${CONFIG.API_BASE_URL}/solicitacao/${window.idSolicitacaoAtual}/pendente`, {
            method: 'PUT',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id_produto_ofertado: produtosOfertadosIds // Envia array
            })
        });
        if (resp.ok) {
            alert('Solicitação de troca realizada com sucesso!');
            window.location.reload();
        } else {
            const erro = await resp.json();
            alert(erro.msg || 'Erro ao solicitar troca.');
        }
    } catch (e) {
        alert('Erro ao conectar ao servidor.');
    }
}

// Função para enviar mensagens no chat (igual doação)
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    const token = localStorage.getItem('access_token');
    if (!token || !window.idSolicitacaoAtual) return;

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/mensagem`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                conteudo_mensagem: message,
                id_solicitacao: window.idSolicitacaoAtual
            })
        });
        if (response.ok) {
            document.getElementById('chat-input').value = '';
            document.dispatchEvent(new Event('DOMContentLoaded'));
        } else {
            alert('Erro ao enviar mensagem.');
        }
    } catch (error) {
        alert('Erro ao conectar ao servidor.');
    }
}

// Função para cancelar solicitação
async function cancelarSolicitacao() {
    const token = localStorage.getItem('access_token');
    if (!window.idSolicitacaoAtual || !token) return;
    if (!confirm('Tem certeza que deseja cancelar a solicitação?')) return;
    try {
        const resp = await fetch(`${CONFIG.API_BASE_URL}/solicitacao/${window.idSolicitacaoAtual}`, {
            method: 'DELETE',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        if (resp.ok) {
            alert('Solicitação cancelada.');
            window.location.href = 'pagina-inicial.html';
        } else {
            const erro = await resp.json();
            alert(erro.msg || 'Erro ao cancelar solicitação.');
        }
    } catch (e) {
        alert('Erro ao conectar ao servidor.');
    }
}

// Aceitar/Recusar solicitação
async function acaoSolicitacao(idSolicitacao, novoStatus) {
    const token = localStorage.getItem('access_token');
    try {
        const resp = await fetch(`${CONFIG.API_BASE_URL}/solicitacao/${idSolicitacao}/acao`, {
            method: 'PUT',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: novoStatus }) // "APROVADA" ou "RECUSADA"
        });
        const result = await resp.json();
        if (resp.ok) {
            alert('Solicitação atualizada com sucesso!');
            window.location.reload();
        } else {
            alert(result.msg || 'Erro ao atualizar solicitação.');
        }
    } catch (e) {
        alert('Erro ao conectar ao servidor.');
    }
}

// Logout
document.getElementById('logout').addEventListener('click', function () {
    localStorage.clear();
    window.location.href = '../index.html';
});