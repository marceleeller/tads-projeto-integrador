// Função para obter os parâmetros da URL
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        id: params.get('id')
    };
}

document.addEventListener('DOMContentLoaded', async () => {
    const { id } = getQueryParams();
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('id_usuario');
    if (!id || !token) {
        alert('Acesso inválido.');
        window.location.href = 'pagina-inicial.html';
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/negociacao/${id}`, {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        if (!response.ok) {
            alert('Erro ao carregar negociação.');
            window.location.href = 'pagina-inicial.html';
            return;
        }
        const data = await response.json();



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

        // Preencher mensagens do chat
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

        // Salva o id da solicitação para uso ao enviar mensagem
        window.idSolicitacaoAtual = data.solicitacao.id_solicitacao;

        // Botões de ação
        const btnContainer = document.querySelector('.text-center.mt-3');
        btnContainer.innerHTML = ''; // Limpa botões antigos

        if (data.solicitacao.status === 'APROVADA') {
            btnContainer.innerHTML = `
                <div class="alert alert-success text-center fw-bold mb-0">
                    Negociação aprovada
                </div>
            `;
        } else if (String(produto.id_usuario) === String(userId)) {
            // Usuário é o dono do produto: mostrar Aceitar/Recusar
            const btnGroup = document.createElement('div');
            btnGroup.className = 'text-center mt-3 d-flex flex-row justify-content-center flex-column align-items-center gap-2';

            const btnAceitar = document.createElement('button');
            btnAceitar.className = 'btn btn-success w-50';
            btnAceitar.textContent = 'Aceitar doação';
            btnAceitar.onclick = async function () {
                await acaoSolicitacao(window.idSolicitacaoAtual, 'APROVADA');
            };

            const btnRecusar = document.createElement('button');
            btnRecusar.className = 'btn btn-danger w-50';
            btnRecusar.textContent = 'Recusar doação';
            btnRecusar.onclick = async function () {
                await acaoSolicitacao(window.idSolicitacaoAtual, 'RECUSADA');
            };

            btnGroup.appendChild(btnAceitar);
            btnGroup.appendChild(btnRecusar);
            btnContainer.appendChild(btnGroup);
        } else {
            const btnGroup = document.createElement('div');
            btnGroup.className = 'text-center mt-3 d-flex flex-row justify-content-center flex-column align-items-center gap-2';

            // Não é dono: mostrar Solicitar Doação ou Solicitação pendente
            const solicitarBtn = document.createElement('button');
            solicitarBtn.className = 'btn btn-success w-50';
            solicitarBtn.id = 'solicitar-btn';
            if (data.solicitacao.status === 'PENDENTE') {
                solicitarBtn.textContent = 'Solicitação pendente';
                solicitarBtn.disabled = true;
            } else {
                solicitarBtn.textContent = 'Solicitar Doação';
                solicitarBtn.disabled = false;
                solicitarBtn.onclick = finalizeDonation;
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

    } catch (error) {
        alert('Erro ao conectar ao servidor.');
        window.location.href = 'pagina-inicial.html';
    }
});

// Exemplo de chamada para aceitar ou rejeitar uma solicitação
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
            // Atualize a tela conforme necessário
        } else {
            alert(result.msg || 'Erro ao atualizar solicitação.');
        }
    } catch (e) {
        alert('Erro ao conectar ao servidor.');
    }
}

// Função para enviar mensagens no chat
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
            // Recarrega as mensagens do chat
            document.getElementById('chat-input').value = '';
            document.dispatchEvent(new Event('DOMContentLoaded'));
        } else {
            alert('Erro ao enviar mensagem.');
        }
    } catch (error) {
        alert('Erro ao conectar ao servidor.');
    }
}

// Função para solicitar doação (ativar solicitação)
async function finalizeDonation() {
    const token = localStorage.getItem('access_token');
    if (!window.idSolicitacaoAtual || !token) return;
    try {
        const resp = await fetch(`${CONFIG.API_BASE_URL}/solicitacao/${window.idSolicitacaoAtual}/pendente`, {
            method: 'PUT',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        if (resp.ok) {
            alert('Solicitação realizada com sucesso!');
            // Atualize a tela ou recarregue os dados
            document.dispatchEvent(new Event('DOMContentLoaded'));
        } else {
            const erro = await resp.json();
            alert(erro.msg || 'Erro ao criar solicitação.');
        }
    } catch (e) {
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

// Logout
document.getElementById('logout').addEventListener('click', function () {
    localStorage.clear();
    window.location.href = '../index.html';
});