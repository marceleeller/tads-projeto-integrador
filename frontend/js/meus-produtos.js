document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('access_token');
    const container = document.getElementById('produtos-container');

    if (!token) {
        container.innerHTML = '<div class="alert alert-warning">Você precisa estar logado para ver seus produtos.</div>';
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/produtos/usuario`, {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        const produtos = await response.json();

        console.log(produtos)

        if (!response.ok) {
            container.innerHTML = `<div class="alert alert-danger">${produtos.msg || 'Erro ao carregar produtos.'}</div>`;
            return;
        }

        if (!produtos.length) {
            container.innerHTML = '<div class="alert alert-info">Você ainda não cadastrou produtos.</div>';
            return;
        }

        container.innerHTML = '';
        produtos.forEach(produto => {
            // Pega a primeira imagem ou um placeholder
            const imgSrc = (produto.imagens && produto.imagens.length > 0)
                ? `${CONFIG.API_BASE_URL.replace('/api', '')}/${produto.imagens[0].url_imagem}`
                : '../assets/placeholder.png';

            // Badge de categoria
            let categoriaBadge = '';
            if (produto.categoria && produto.categoria.nome_categoria) {
                let nomeCategoria = produto.categoria.nome_categoria;
                if (nomeCategoria.toUpperCase() === 'DOAÇÃO') nomeCategoria = 'Doação';
                if (nomeCategoria.toUpperCase() === 'TROCA') nomeCategoria = 'Troca';
                categoriaBadge = `<span class="badge bg-${nomeCategoria === 'Troca' ? 'warning' : 'success'} me-2">${nomeCategoria}</span>`;
            }

            // Busca a solicitação ativa (PENDENTE ou APROVADA)
            let solicitacaoAtiva = null;
            if (produto.solicitacoes && produto.solicitacoes.length > 0) {
                solicitacaoAtiva = produto.solicitacoes.find(s =>
                    s.status === 'PENDENTE' || s.status === 'APROVADA'
                );
            }

            // Busca solicitação CANCELADA feita pelo usuário logado (não dono)
            const userId = localStorage.getItem('id_usuario');
            let solicitacaoCanceladaDoUsuario = null;
            if (produto.solicitacoes && produto.solicitacoes.length > 0) {
                solicitacaoCanceladaDoUsuario = produto.solicitacoes.find(s =>
                    s.status === 'CANCELADA' && String(s.id_usuario_solicitante) === String(userId)
                );
            }

            // Badge de status da solicitação
            let statusBadge = '';
            if (solicitacaoAtiva) {
                if (solicitacaoAtiva.status === 'PENDENTE') {
                    statusBadge = '<span class="badge bg-warning text-dark">Pendente</span>';
                } else if (solicitacaoAtiva.status === 'APROVADA') {
                    statusBadge = '<span class="badge bg-success">Aprovada</span>';
                }
            } else if (solicitacaoCanceladaDoUsuario && String(produto.id_usuario) !== String(userId)) {
                statusBadge = '<span class="badge bg-danger text-white">Cancelada</span>';
            } else {
                statusBadge = '<span class="badge bg-primary">Disponível</span>';
            }

            // Lógica dos botões
            let botoes = `
                <a href="cadastro-produto.html?id=${produto.id_produto}" class="btn btn-primary w-50">Editar</a>
                <button class="btn btn-outline-secondary w-50" onclick="excluirProduto(${produto.id_produto})">Excluir</button>
            `;

            const temNegociacaoAtiva = !!solicitacaoAtiva;

            if (temNegociacaoAtiva) {
                const isTroca = produto.categoria && (
                    produto.categoria.tipo === 'TROCA' ||
                    (produto.categoria.nome_categoria && produto.categoria.nome_categoria.toUpperCase().includes('TROCA'))
                );
                const urlNegociacao = isTroca
                    ? `negociacao-troca.html?id=${produto.id_produto}`
                    : `negociacao-doacao.html?id=${produto.id_produto}`;
                botoes = `<a href="${urlNegociacao}" class="btn btn-primary w-100">Ver Negociação</a>`;
            } else if (solicitacaoCanceladaDoUsuario && String(produto.id_usuario) !== String(userId)) {
                // Não mostra botão algum
                botoes = '';
            }

            container.innerHTML += `
                <div class="col-md-4">
                    <div class="card shadow">
                        <img src="${imgSrc}" class="card-img-top img-fluid" alt="${produto.nome_produto}" style="height: 200px; object-fit: cover;">
                        <div class="card-body">
                            <h5 class="card-title">${produto.nome_produto}</h5>
                            <p class="card-text">${produto.descricao}</p>
                            <div>${categoriaBadge}</div>
                            <div>
                                <small>Status:</small>
                                ${statusBadge}
                            </div>
                            <div class="d-flex gap-2 mt-3">
                                ${botoes}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
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