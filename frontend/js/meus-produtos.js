document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('access_token');
    const nomeUsuario = localStorage.getItem('nome_usuario');
    const container = document.getElementById('produtos-container');

    if (nomeUsuario) {
        const spanBemVindo = document.getElementById('bem-vindo-usuario');
        if (spanBemVindo) {
            spanBemVindo.textContent = `Bem-vindo(a), ${nomeUsuario}`;
        }
    }

    if (!token) {
        if (container) {
            container.innerHTML = '<div class="alert alert-warning">Você precisa estar logado para ver seus produtos. Redirecionando para login...</div>';
        }
        setTimeout(() => {
            window.location.href = '../index.html';
        }, 3000);
        return;
    }

    // Referências aos filtros (certifique-se que os IDs no HTML correspondem)
    const filtroNomeInput = document.getElementById('filtro-nome');
    const filtroStatusProdutoSelect = document.getElementById('filtro-status-produto'); // ID ajustado para o novo filtro de status
    const filtroCategoriaSelect = document.getElementById('filtro-categoria');

    let todosOsProdutosDoUsuario = []; // Para armazenar os produtos buscados

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/produtos/usuario`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (!response.ok) {
            const erroData = await response.json().catch(() => null);
            throw new Error(erroData?.msg || `Erro HTTP ${response.status} ao carregar produtos.`);
        }

        todosOsProdutosDoUsuario = await response.json();

        if (!todosOsProdutosDoUsuario.length) {
            if (container) {
                container.innerHTML = '<div class="alert alert-info">Você ainda não cadastrou produtos gerenciáveis ou todos os seus produtos já foram transacionados.</div>';
            }
            return;
        }

        renderizarListaProdutos(); // Renderização inicial

    } catch (error) {
        console.error("Erro ao buscar produtos do usuário:", error);
        if (container) {
            container.innerHTML = `<div class="alert alert-danger">${error.message || 'Erro ao conectar ao servidor para carregar seus produtos.'}</div>`;
        }
    }

    function renderizarListaProdutos() {
        if (!container) return;

        const nomeFiltro = filtroNomeInput ? filtroNomeInput.value.toLowerCase() : '';
        const statusFiltro = filtroStatusProdutoSelect ? filtroStatusProdutoSelect.value : ''; // e.g., DISPONIVEL, PENDENTE
        const categoriaFiltro = filtroCategoriaSelect ? filtroCategoriaSelect.value.toUpperCase() : ''; // e.g., TROCA, DOAÇÃO

        container.innerHTML = '';
        let algumProdutoExibido = false;

        todosOsProdutosDoUsuario.forEach(produto => {
            const nomeProdutoOriginal = produto.nome_produto || '';
            const nomeProdutoLowerCase = nomeProdutoOriginal.toLowerCase();
            const categoriaProduto = produto.categoria?.nome_categoria?.toUpperCase() || '';

            const temSolicitacoesPendentes = produto.solicitacoes_pendentes_nele && produto.solicitacoes_pendentes_nele.length > 0;
            const statusDisplayProduto = temSolicitacoesPendentes ? 'PENDENTE' : 'DISPONIVEL';

            // Aplicar filtros
            if (nomeFiltro && !nomeProdutoLowerCase.includes(nomeFiltro)) return;
            if (statusFiltro && statusDisplayProduto !== statusFiltro) return;
            if (categoriaFiltro && categoriaProduto !== categoriaFiltro) return;

            container.innerHTML += criarCardProdutoHtml(produto, temSolicitacoesPendentes);
            algumProdutoExibido = true;
        });

        if (!algumProdutoExibido && todosOsProdutosDoUsuario.length > 0) {
            container.innerHTML = '<div class="alert alert-info w-100 text-center">Nenhum produto encontrado com os filtros aplicados.</div>';
        } else if (!algumProdutoExibido && todosOsProdutosDoUsuario.length === 0) {
            // A mensagem de "nenhum produto" já é tratada antes do loop
        }
    }

    // Event listeners para os filtros
    if (filtroNomeInput) filtroNomeInput.addEventListener('input', renderizarListaProdutos);
    if (filtroStatusProdutoSelect) filtroStatusProdutoSelect.addEventListener('change', renderizarListaProdutos);
    if (filtroCategoriaSelect) filtroCategoriaSelect.addEventListener('change', renderizarListaProdutos);

    // Botão de Logout
    const logoutButton = document.getElementById('logout');
    if (logoutButton) {
        logoutButton.addEventListener('click', function () {
            localStorage.clear();
            window.location.href = '../index.html';
        });
    }
});

function criarCardProdutoHtml(produto, temSolicitacoesPendentes) {
    const imgSrc = (produto.imagens && produto.imagens.length > 0 && produto.imagens[0].url_imagem)
        ? `${CONFIG.API_BASE_URL.replace('/api', '')}/${produto.imagens[0].url_imagem}` // Adicionada verificação para url_imagem
        : '../assets/placeholder.png';

    let categoriaBadge = '';
    if (produto.categoria && produto.categoria.nome_categoria) {
        let nomeCategoria = produto.categoria.nome_categoria;
        const nomeCatUpper = nomeCategoria.toUpperCase();
        const displayNomeCat = nomeCatUpper === 'DOAÇÃO' ? 'Doação' : (nomeCatUpper === 'TROCA' ? 'Troca' : nomeCategoria);
        const badgeClass = nomeCatUpper === 'TROCA' ? 'bg-warning text-dark' : 'bg-success';
        categoriaBadge = `<span class="badge ${badgeClass} me-2">${displayNomeCat}</span>`;
    }

    let statusBadgeHtml = '';
    let botoesHtml = '';
    let dataInfoHtml = ''; // Para informações adicionais de data

    if (temSolicitacoesPendentes) {
        statusBadgeHtml = `<span class="badge bg-info">Com Propostas (${produto.solicitacoes_pendentes_nele.length})</span>`;
        const solicitacaoPrincipal = produto.solicitacoes_pendentes_nele[0]; // Pega a primeira para o link

        const tipoNegociacao = produto.categoria?.nome_categoria?.toUpperCase() === 'TROCA' ? 'negociacao-troca' : 'negociacao-doacao';

        // A negociação é sobre 'produto.id_produto' (o produto do usuário que é o desejado na solicitação)
        // e precisa do 'solicitacaoPrincipal.id_solicitacao'
        botoesHtml = `<a href="./${tipoNegociacao}.html?id=${produto.id_produto}&solicitacao_id=${solicitacaoPrincipal.id_solicitacao}" class="btn btn-info w-100">Ver Propostas</a>`;

        // Opcional: adicionar botões de editar/excluir desabilitados
        botoesHtml += `
            <div class="d-flex gap-2 mt-2">
                <a href="cadastro-produto.html?id=${produto.id_produto}" class="btn btn-sm btn-outline-primary w-50 disabled" aria-disabled="true" title="Edição desabilitada durante negociação">Editar</a>
                <button class="btn btn-sm btn-outline-danger w-50" disabled title="Exclusão desabilitada durante negociação">Excluir</button>
            </div>
        `;

        if (solicitacaoPrincipal.data_solicitacao) {
            let data = new Date(solicitacaoPrincipal.data_solicitacao);
            // O ajuste de fuso horário (-3 horas) pode ser necessário dependendo de como as datas são armazenadas e exibidas.
            // Exemplo: data.setHours(data.getHours() - 3); 
            dataInfoHtml = `<div><small class="text-muted" style="font-size: 0.85em;">Última proposta: ${data.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</small></div>`;
        }
    } else {
        // Produto disponível para edição/exclusão
        statusBadgeHtml = '<span class="badge bg-primary">Disponível</span>';
        botoesHtml = `
            <a href="cadastro-produto.html?id=${produto.id_produto}" class="btn btn-primary w-50">Editar</a>
            <button class="btn btn-outline-danger w-50" onclick="excluirProduto(${produto.id_produto})">Excluir</button>
        `;
    }

    const descricaoCurta = produto.descricao ? (produto.descricao.length > 80 ? produto.descricao.substring(0, 80) + '...' : produto.descricao) : 'Sem descrição.';

    return `
        <div class="col-md-4 mb-4">
            <div class="card shadow h-100 d-flex flex-column">
                <img src="${imgSrc}" class="card-img-top img-fluid" alt="${produto.nome_produto || 'Imagem do Produto'}" style="height: 200px; object-fit: cover;">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">${produto.nome_produto || 'Produto sem nome'}</h5>
                    <p class="card-text" style="flex-grow: 1; min-height: 60px;">${descricaoCurta}</p>
                    <div>${categoriaBadge}</div>
                    <div class="mt-1">
                        <small>Status:</small>
                        ${statusBadgeHtml}
                    </div>
                    ${dataInfoHtml}
                    <div class="d-flex gap-2 mt-auto pt-2">
                        ${botoesHtml}
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function excluirProduto(id_produto) {
    if (!confirm('Tem certeza que deseja excluir este produto? Esta ação não pode ser desfeita.')) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('Sessão expirada. Por favor, faça login novamente.');
        window.location.href = '../index.html';
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/produto/${id_produto}`, {
            method: 'DELETE',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        const result = await response.json();
        if (response.ok) {
            alert(result.msg || 'Produto excluído com sucesso!');
            // Recarregar a lista de produtos para refletir a exclusão
            window.location.reload(); // Simples, mas efetivo. Ou pode remover o card do DOM.
        } else {
            alert(result.msg || 'Erro ao excluir produto. Verifique se ele não está em negociações ativas ou se já foi transacionado.');
        }
    } catch (error) {
        console.error('Erro ao conectar ao servidor para excluir produto:', error);
        alert('Erro ao conectar ao servidor.');
    }
}