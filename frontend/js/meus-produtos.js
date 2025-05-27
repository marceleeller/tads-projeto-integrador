document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('access_token');
    const container = document.getElementById('produtos-container');

    if (!token) {
        container.innerHTML = '<div class="alert alert-warning">Você precisa estar logado para ver seus produtos.</div>';
        return;
    }

    const nomeUsuario = localStorage.getItem('nome_usuario');
    if (nomeUsuario) {
        const spanBemVindo = document.getElementById('bem-vindo-usuario');
        if (spanBemVindo) {
            spanBemVindo.textContent = `Bem-vindo(a), ${nomeUsuario}`;
        }
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/produtos/usuario`, {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        const produtos = await response.json();

        if (!response.ok) {
            container.innerHTML = `<div class="alert alert-danger">${produtos.msg || 'Erro ao carregar produtos.'}</div>`;
            return;
        }

        if (!produtos.length) {
            container.innerHTML = '<div class="alert alert-info">Você ainda não cadastrou produtos.</div>';
            return;
        }
        const idUsuarioLogado = localStorage.getItem('id_usuario');

        // 1. Coletar IDs de produtos ofertados em negociações ativas
        const produtosOfertadosEmNegociacaoAtiva = new Set();
        produtos.forEach(produto => {
            if (produto.solicitacoes && produto.solicitacoes.length > 0) {
                produto.solicitacoes.forEach(solicitacao => {
                    if (
                        ['PENDENTE', 'APROVADA'].includes(solicitacao.status) &&
                        solicitacao.produtos_ofertados &&
                        solicitacao.produtos_ofertados.length > 0
                    ) {
                        solicitacao.produtos_ofertados.forEach(idProd => {
                            produtosOfertadosEmNegociacaoAtiva.add(idProd);
                        });
                    }
                });
            }
        });

        // 2. Monta a lista de cards
        const cards = [];
        produtos.forEach(produto => {
            if (!produto.solicitacoes || produto.solicitacoes.length === 0) {
                // Só adiciona como editável se for do usuário logado E não está em negociação ativa
                if (
                    produto.id_usuario == idUsuarioLogado &&
                    !produtosOfertadosEmNegociacaoAtiva.has(produto.id_produto)
                ) {
                    cards.push({ produto, solicitacao: null });
                }
            } else {
                // Adiciona todas as solicitações que não são PROCESSANDO
                produto.solicitacoes.forEach(solicitacao => {
                    if (solicitacao.status !== 'PROCESSANDO') {
                        cards.push({ produto, solicitacao });
                    }
                });

                // Se todas as solicitações forem RECUSADA ou CANCELADA,
                // só adiciona como editável se for do usuário logado E não está em negociação ativa
                const todasRecusadasOuCanceladas = produto.solicitacoes.every(solicitacao =>
                    solicitacao.status === 'RECUSADA' || solicitacao.status === 'CANCELADA'
                );
                if (
                    todasRecusadasOuCanceladas &&
                    produto.id_usuario == idUsuarioLogado &&
                    !produtosOfertadosEmNegociacaoAtiva.has(produto.id_produto)
                ) {
                    cards.push({ produto, solicitacao: null });
                }
            }
        });

        // Ordenação: edição (sem solicitação) > pendente > outros (mais recentes primeiro)
        cards.sort((a, b) => {
            if (!a.solicitacao && b.solicitacao) return -1;
            if (a.solicitacao && !b.solicitacao) return 1;
            if (a.solicitacao && b.solicitacao) {
                if (a.solicitacao.status === 'PENDENTE' && b.solicitacao.status !== 'PENDENTE') return -1;
                if (a.solicitacao.status !== 'PENDENTE' && b.solicitacao.status === 'PENDENTE') return 1;
                return new Date(b.solicitacao.data_solicitacao) - new Date(a.solicitacao.data_solicitacao);
            }
            return 0;
        });

        function renderProduto(produto, solicitacao) {
            const imgSrc = (produto.imagens && produto.imagens.length > 0)
                ? `${CONFIG.API_BASE_URL.replace('/api', '')}/${produto.imagens[0].url_imagem}`
                : '../assets/placeholder.png';

            let categoriaBadge = '';
            if (produto.categoria && produto.categoria.nome_categoria) {
                let nomeCategoria = produto.categoria.nome_categoria;
                if (nomeCategoria.toUpperCase() === 'DOAÇÃO') nomeCategoria = 'Doação';
                if (nomeCategoria.toUpperCase() === 'TROCA') nomeCategoria = 'Troca';
                categoriaBadge = `<span class="badge bg-${nomeCategoria === 'Troca' ? 'warning' : 'success'} me-2">${nomeCategoria}</span>`;
            }

            let statusBadge = '<span class="badge bg-primary">Disponível</span>';
            if (solicitacao) {
                switch (solicitacao.status) {
                    case 'PENDENTE':
                        statusBadge = '<span class="badge bg-warning text-dark">Pendente</span>';
                        break;
                    case 'APROVADA':
                        statusBadge = '<span class="badge bg-success">Aprovada</span>';
                        break;
                    case 'RECUSADA':
                        statusBadge = '<span class="badge bg-danger text-white">Recusada</span>';
                        break;
                    case 'CANCELADA':
                        statusBadge = '<span class="badge bg-secondary text-white">Cancelada</span>';
                        break;
                }
            }

            // Lógica dos botões
            let botoes = `
                <a href="cadastro-produto.html?id=${produto.id_produto}" class="btn btn-primary w-50">Editar</a>
                <button class="btn btn-outline-secondary w-50" onclick="excluirProduto(${produto.id_produto})">Excluir</button>
            `;

            let espacoAcimaBotoes = '';
            if (!solicitacao) {
                espacoAcimaBotoes = `<div style="height:38px"></div>`;
            }

            if (solicitacao) {
                const isTroca = produto.categoria && (
                    produto.categoria.tipo === 'TROCA' ||
                    (produto.categoria.nome_categoria && produto.categoria.nome_categoria.toUpperCase().includes('TROCA'))
                );
                const urlNegociacao = isTroca
                    ? `negociacao-troca.html?id=${produto.id_produto}`
                    : `negociacao-doacao.html?id=${produto.id_produto}`;

                if (['PENDENTE', 'APROVADA'].includes(solicitacao.status)) {
                    botoes = `<a href="${urlNegociacao}" class="btn btn-primary w-100">Ver Negociação</a>`;
                    espacoAcimaBotoes = '';
                } else {
                    botoes = `<div style="height:38px"></div>`;
                    espacoAcimaBotoes = '';
                }
            }

            let dataSolicitacaoHtml = '';
            if (solicitacao && solicitacao.data_solicitacao) {
                let data = new Date(solicitacao.data_solicitacao);
                // Corrige para o horário de Brasília subtraindo 3 horas
                data.setHours(data.getHours() - 3);
                const dataFormatada = data.toLocaleString('pt-BR');
                dataSolicitacaoHtml = `<div><small class="text-muted" style="font-size: 0.85em;">Solicitação em: ${dataFormatada}</small></div>`;
            }

            return `
                <div class="col-md-4">
                    <div class="card shadow h-100 d-flex flex-column">
                        <img src="${imgSrc}" class="card-img-top img-fluid" alt="${produto.nome_produto}" style="height: 200px; object-fit: cover;">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">${produto.nome_produto}</h5>
                            <p class="card-text">${produto.descricao}</p>
                            <div>${categoriaBadge}</div>
                            <div>
                                <small>Status:</small>
                                ${statusBadge}
                            </div>
                            ${dataSolicitacaoHtml}
                            ${espacoAcimaBotoes}
                            <div class="d-flex gap-2 mt-3 mt-auto">
                                ${botoes}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        function renderTodosProdutos() {
            const nomeFiltro = document.getElementById('filtro-nome').value.toLowerCase();
            const statusFiltro = document.getElementById('filtro-status').value;
            const categoriaFiltro = document.getElementById('filtro-categoria').value;

            const filtrados = cards.filter(card => {
                const produto = card.produto;
                const solicitacao = card.solicitacao;

                // Filtro por nome
                if (nomeFiltro && !produto.nome_produto.toLowerCase().includes(nomeFiltro)) return false;

                // Filtro por status
                let status = 'DISPONIVEL';
                if (solicitacao && solicitacao.status) status = solicitacao.status;
                if (statusFiltro && status !== statusFiltro) return false;

                // Filtro por categoria
                let categoria = '';
                if (produto.categoria && produto.categoria.nome_categoria) {
                    categoria = produto.categoria.nome_categoria.toUpperCase();
                }
                if (categoriaFiltro && categoria !== categoriaFiltro) return false;

                return true;
            });

            container.innerHTML = '';
            filtrados.forEach(card => {
                container.innerHTML += renderProduto(card.produto, card.solicitacao);
            });
        }

        renderTodosProdutos();
        document.getElementById('filtro-nome').addEventListener('input', renderTodosProdutos);
        document.getElementById('filtro-status').addEventListener('change', renderTodosProdutos);
        document.getElementById('filtro-categoria').addEventListener('change', renderTodosProdutos);

    } catch (error) {
        container.innerHTML = '<div class="alert alert-danger">Erro ao conectar ao servidor.</div>';
    }
});

// Função para excluir produto (mantida)
async function excluirProduto(id_produto) {
    if (!confirm('Tem certeza que deseja excluir este produto?')) return;
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/produto/${id_produto}`, {
            method: 'DELETE',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        const result = await response.json();
        if (response.ok) {
            alert('Produto excluído com sucesso!');
            window.location.reload();
        } else {
            alert(result.msg || 'Erro ao excluir produto.');
        }
    } catch (error) {
        alert('Erro ao conectar ao servidor.');
    }
}

document.querySelector('#logout').addEventListener('click', function () {
    localStorage.clear();
    window.location.href = '../index.html';
});