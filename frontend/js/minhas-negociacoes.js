document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('access_token');
    const nomeUsuario = localStorage.getItem('nome_usuario');
    const userId = parseInt(localStorage.getItem('id_usuario'), 10); // ID do usuário logado como número

    const container = document.getElementById('negociacoes-list-container');
    const loadingIndicator = document.getElementById('loading-negociacoes');
    const nenhumaNegociacaoMsg = document.getElementById('nenhuma-negociacao');

    // Elementos de filtro
    const filtroStatusSelect = document.getElementById('filtro-status-negociacao');
    const filtroTipoSelect = document.getElementById('filtro-tipo-negociacao');
    const filtroPapelSelect = document.getElementById('filtro-papel-usuario');

    let todasAsNegociacoes = []; // Para armazenar os dados brutos da API

    if (nomeUsuario) {
        const spanBemVindo = document.getElementById('bem-vindo-usuario');
        if (spanBemVindo) {
            spanBemVindo.textContent = `Bem-vindo(a), ${nomeUsuario}`;
        }
    }

    if (!token) {
        if (container) container.innerHTML = '<div class="alert alert-warning">Você precisa estar logado para ver suas negociações. Redirecionando para login...</div>';
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        setTimeout(() => { window.location.href = '../index.html'; }, 3000);
        return;
    }

    async function carregarNegociacoes() {
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (container) container.innerHTML = '';
        if (nenhumaNegociacaoMsg) nenhumaNegociacaoMsg.style.display = 'none';

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/usuario/negociacoes`, {
                headers: { 'Authorization': 'Bearer ' + token }
            });

            if (!response.ok) {
                const erroData = await response.json().catch(() => null);
                throw new Error(erroData?.msg || `Erro HTTP ${response.status} ao carregar negociações.`);
            }

            todasAsNegociacoes = await response.json();
            renderizarNegociacoesFiltradas();

        } catch (error) {
            console.error("Erro ao buscar negociações:", error);
            if (container) container.innerHTML = `<div class="alert alert-danger">${error.message || 'Erro ao conectar ao servidor.'}</div>`;
        } finally {
            if (loadingIndicator) loadingIndicator.style.display = 'none';
        }
    }

    function renderizarNegociacoesFiltradas() {
        // Obtém o ID do usuário logado. Certifique-se que 'userId' esteja acessível aqui.
        // No nosso código anterior, 'userId' era definido no escopo do DOMContentLoaded.
        const userId = parseInt(localStorage.getItem('id_usuario'), 10);
        if (!container) { // container da lista de negociações
            console.error("Elemento container da lista de negociações não encontrado.");
            return;
        }
        container.innerHTML = ''; // Limpa o conteúdo anterior
        const statusFiltro = filtroStatusSelect ? filtroStatusSelect.value : '';
        const tipoFiltro = filtroTipoSelect ? filtroTipoSelect.value.toUpperCase() : ''; // TROCA, DOAÇÃO
        const papelFiltro = filtroPapelSelect ? filtroPapelSelect.value : ''; // SOLICITANTE, PROPRIETARIO

        const negociacoesFiltradas = todasAsNegociacoes.filter(negociacao => {
            // 1. Filtro por Status da Negociação
            if (statusFiltro && negociacao.status !== statusFiltro) {
                return false;
            }

            // 2. Filtro por Tipo de Negociação (Troca/Doação)
            // Deriva o tipo da negociação a partir dos dados disponíveis
            const tipoNegociacaoAtual = (
                negociacao.tipo_solicitacao ||
                negociacao.produto_desejado?.categoria?.nome_categoria ||
                ''
            ).toUpperCase();
            if (tipoFiltro && tipoNegociacaoAtual !== tipoFiltro) {
                return false;
            }

            // 3. Filtro por Papel do Usuário na Negociação
            if (papelFiltro) {
                const idSolicitanteApi = negociacao.id_usuario_solicitante;
                const idDonoProdutoDesejadoApi = negociacao.produto_desejado?.proprietario_details?.id_usuario;

                if (papelFiltro === 'SOLICITANTE') {
                    if (idSolicitanteApi !== userId) {
                        return false;
                    }
                } else if (papelFiltro === 'PROPRIETARIO') {
                    // Se o produto desejado ou os detalhes do proprietário não existirem,
                    // ou se o ID do proprietário não for o do usuário logado, filtra.
                    if (!idDonoProdutoDesejadoApi || idDonoProdutoDesejadoApi !== userId) {
                        return false;
                    }
                }
            }

            // Se passou por todos os filtros, o item é incluído
            return true;
        });

        if (negociacoesFiltradas.length === 0) {
            if (nenhumaNegociacaoMsg) { // nenhumaNegociacaoMsg é o elemento HTML para a mensagem
                nenhumaNegociacaoMsg.style.display = 'block';
            }
        } else {
            if (nenhumaNegociacaoMsg) {
                nenhumaNegociacaoMsg.style.display = 'none';
            }
            negociacoesFiltradas.forEach(negociacao => {
                // Passa 'userId' para a função de criação do card, pois ela também o utiliza
                // para determinar a exibição de informações ou botões.
                container.innerHTML += criarCardNegociacaoHtml(negociacao, userId);
            });
        }
    }

    // Event Listeners para os filtros
    if (filtroStatusSelect) filtroStatusSelect.addEventListener('change', renderizarNegociacoesFiltradas);
    if (filtroTipoSelect) filtroTipoSelect.addEventListener('change', renderizarNegociacoesFiltradas);
    if (filtroPapelSelect) filtroPapelSelect.addEventListener('change', renderizarNegociacoesFiltradas);

    // Carregar negociações ao iniciar
    await carregarNegociacoes();

    // Botão de Logout
    const logoutButton = document.getElementById('logout');
    if (logoutButton) {
        logoutButton.addEventListener('click', function () {
            localStorage.clear();
            window.location.href = '../index.html';
        });
    }
});

function criarCardNegociacaoHtml(negociacao, currentUserId) {
    // CORREÇÃO: Acessar 'produto_desejado' e 'usuario_solicitante' diretamente
    const produtoDesejado = negociacao.produto_desejado;
    const solicitante = negociacao.usuario_solicitante;

    // Esta verificação agora deve funcionar corretamente
    if (!produtoDesejado) {
        console.error("Dados do produto desejado ausentes na negociação:", negociacao);
        return `<div class="card mb-3"><div class="card-body"><p class="text-danger">Erro: Dados do produto desejado não encontrados para esta negociação (ID: ${negociacao.id_solicitacao}).</p></div></div>`;
    }

    const imgSrc = (produtoDesejado.imagens && produtoDesejado.imagens.length > 0 && produtoDesejado.imagens[0].url_imagem)
        ? `${CONFIG.API_BASE_URL.replace('/api', '')}/${produtoDesejado.imagens[0].url_imagem}`
        : '../assets/placeholder.png';

    // A API já envia 'tipo_solicitacao', ou podemos derivá-lo se necessário
    const tipoNegociacao = (negociacao.tipo_solicitacao || produtoDesejado.categoria?.nome_categoria || 'N/D').toUpperCase();
    const displayTipo = tipoNegociacao === 'DOAÇÃO' ? 'Doação' : (tipoNegociacao === 'TROCA' ? 'Troca' : tipoNegociacao);

    // CORREÇÃO: Acessar 'proprietario_details' dentro do objeto produtoDesejado
    const donoProdutoDesejado = produtoDesejado.proprietario_details;

    let comQuemNegociaLabel = '';
    let comQuemNegociaNome = 'N/D';

    const euSouSolicitante = solicitante && solicitante.id_usuario === currentUserId;
    const euSouDonoDoProdutoDesejado = donoProdutoDesejado && donoProdutoDesejado.id_usuario === currentUserId;

    if (euSouSolicitante && donoProdutoDesejado) {
        comQuemNegociaLabel = 'Dono do Produto:';
        comQuemNegociaNome = donoProdutoDesejado.nome_usuario || 'Desconhecido';
    } else if (euSouDonoDoProdutoDesejado && solicitante) {
        comQuemNegociaLabel = 'Solicitante:';
        comQuemNegociaNome = solicitante.nome_usuario || 'Desconhecido';
    }
    // (Não precisa do caso 'else if (solicitante && donoProdutoDesejado)' pois um dos dois acima deve ser verdadeiro para o usuário logado)

    let statusBadgeClass = 'bg-secondary';
    switch (negociacao.status) {
        case 'PENDENTE': statusBadgeClass = 'bg-warning text-dark'; break;
        case 'APROVADA': statusBadgeClass = 'bg-success'; break;
        case 'RECUSADA': statusBadgeClass = 'bg-danger'; break;
        case 'CANCELADA': statusBadgeClass = 'bg-secondary'; break;
        case 'PROCESSANDO': statusBadgeClass = 'bg-info text-dark'; break;
    }

    const dataSolicitacao = new Date(negociacao.data_solicitacao).toLocaleString('pt-BR', {
        day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });

    // Lógica dos Botões de Ação (permanece a mesma, mas agora usa as variáveis corretas)
    let acoesHtml = '';
    const urlDetalhes = `./${tipoNegociacao.toLowerCase() === 'troca' ? 'negociacao-troca' : 'negociacao-doacao'}.html?id=${produtoDesejado.id_produto}&solicitacao_id=${negociacao.id_solicitacao}`;

    acoesHtml += `<a href="${urlDetalhes}" class="btn btn-primary btn-sm w-100 mb-2">Ver Detalhes / Chat</a>`;

    if (negociacao.status === 'PENDENTE') {
        if (euSouDonoDoProdutoDesejado) {
            acoesHtml += `
                <button class="btn btn-success btn-sm w-100 mb-2" onclick="responderSolicitacao(${negociacao.id_solicitacao}, 'APROVADA', '${displayTipo}')">Aceitar</button>
                <button class="btn btn-danger btn-sm w-100" onclick="responderSolicitacao(${negociacao.id_solicitacao}, 'RECUSADA', '${displayTipo}')">Recusar</button>
            `;
        } else if (euSouSolicitante) {
            acoesHtml += `<button class="btn btn-warning btn-sm w-100 text-dark" onclick="cancelarMinhaSolicitacao(${negociacao.id_solicitacao})">Cancelar Solicitação</button>`;
        }
    }

    // Produtos Ofertados (se for troca)
    let produtosOfertadosHtml = '';
    if (tipoNegociacao === 'TROCA' && negociacao.produtos_ofertados_details && negociacao.produtos_ofertados_details.length > 0) {
        produtosOfertadosHtml += `<div class="mt-3"><strong>Produtos Ofertados na Troca:</strong><ul class="list-unstyled mb-0 row">`;
        negociacao.produtos_ofertados_details.forEach(pOfertado => {
            const imgOfertadoSrc = (pOfertado.imagens && pOfertado.imagens.length > 0 && pOfertado.imagens[0].url_imagem)
                ? `${CONFIG.API_BASE_URL.replace('/api', '')}/${pOfertado.imagens[0].url_imagem}`
                : '../assets/placeholder.png';
            produtosOfertadosHtml += `
                <li class="col-6 col-sm-4 col-md-3 mb-2 text-center">
                    <img src="${imgOfertadoSrc}" alt="${pOfertado.nome_produto || 'Produto ofertado'}" class="img-thumbnail mb-1" style="width: 60px; height: 60px; object-fit: cover;">
                    <small class="d-block text-muted" style="font-size: 0.8em;">${pOfertado.nome_produto || 'N/D'}</small>
                </li>
            `;
        });
        produtosOfertadosHtml += `</ul></div>`;
    }

    return `
        <div class="card negociacao-item mb-3 shadow-sm">
            <div class="card-header d-flex justify-content-between align-items-center flex-wrap">
                <h6 class="mb-0 me-2 small">Negociação #${negociacao.id_solicitacao} - ${displayTipo}</h6>
                <span class="badge ${statusBadgeClass}">${negociacao.status}</span>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-lg-2 col-md-3 text-center mb-2 mb-md-0">
                        <img src="${imgSrc}" alt="Produto: ${produtoDesejado.nome_produto || 'Produto sem nome'}" class="img-fluid rounded" style="max-height: 100px; object-fit: cover;">
                    </div>
                    <div class="col-lg-7 col-md-6">
                        <h5 class="card-title mb-1" style="font-size: 1.1rem;">${produtoDesejado.nome_produto || 'Produto sem nome'}</h5>
                        ${comQuemNegociaNome !== 'N/D' ? `<p class="card-text mb-1"><small><strong>${comQuemNegociaLabel}</strong> ${comQuemNegociaNome}</small></p>` : ''}
                        <p class="card-text mb-0"><small class="text-muted">Data da Solicitação: ${dataSolicitacao}</small></p>
                        ${produtosOfertadosHtml}
                    </div>
                    <div class="col-lg-3 col-md-3 d-flex flex-column justify-content-center align-items-stretch">
                        ${acoesHtml}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Funções de Ação (você precisará implementá-las, similares às de negociacao-*.js)
async function responderSolicitacao(idSolicitacao, novaAcao, tipoNegociacao) {
    const token = localStorage.getItem('access_token');
    if (!confirm(`Tem certeza que deseja "${novaAcao === 'APROVADA' ? 'ACEITAR' : 'RECUSAR'}" esta ${tipoNegociacao.toLowerCase()}?`)) return;

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/solicitacao/${idSolicitacao}/acao`, {
            method: 'PUT',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: novaAcao }) // Backend espera 'APROVADA' ou 'RECUSADA'
        });
        const result = await response.json();
        if (response.ok) {
            alert(`Solicitação ${novaAcao.toLowerCase().replace('a', 'ada')} com sucesso!`);
            // Recarregar a lista de negociações para refletir a mudança
            document.dispatchEvent(new CustomEvent('reloadNegociacoes'));
        } else {
            alert(result.msg || 'Erro ao responder à solicitação.');
        }
    } catch (error) {
        console.error('Erro ao responder solicitação:', error);
        alert('Erro ao conectar ao servidor.');
    }
}

async function cancelarMinhaSolicitacao(idSolicitacao) {
    const token = localStorage.getItem('access_token');
    if (!confirm('Tem certeza que deseja cancelar esta solicitação?')) return;

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/solicitacao/${idSolicitacao}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (response.ok) {
            alert('Solicitação cancelada com sucesso!');
            // Recarregar a lista de negociações
            document.dispatchEvent(new CustomEvent('reloadNegociacoes'));
        } else {
            const result = await response.json().catch(() => null);
            alert(result?.msg || 'Erro ao cancelar solicitação.');
        }
    } catch (error) {
        console.error('Erro ao cancelar solicitação:', error);
        alert('Erro ao conectar ao servidor.');
    }
}

// Event listener para recarregar negociações (usado pelas funções de ação)
document.addEventListener('reloadNegociacoes', async () => {
    const event = new Event('DOMContentLoaded'); // Recria o evento para simular o recarregamento
    document.dispatchEvent(event); // Dispara o evento para que a função anonima de DOMContentLoaded seja executada novamente
    // Melhor seria chamar a função de carregar e renderizar diretamente
    // Ex: await carregarNegociacoes(); // Se 'carregarNegociacoes' estiver no escopo global ou acessível
});