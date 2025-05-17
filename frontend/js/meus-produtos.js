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

        console.log(produtos);

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
                // Deixa "Troca" ou "Doação" com a primeira letra maiúscula e o resto minúsculo
                if (nomeCategoria.toUpperCase() === 'DOAÇÃO') nomeCategoria = 'Doação';
                if (nomeCategoria.toUpperCase() === 'TROCA') nomeCategoria = 'Troca';
                categoriaBadge = `<span class="badge bg-${nomeCategoria === 'Troca' ? 'warning' : 'success'} me-2">${nomeCategoria}</span>`;
            }

            // Badge de status da solicitação
            let statusBadge = '';
            const statusSolicitacao = produto.status_solicitacao;
            if (statusSolicitacao === 'PENDENTE') {
                statusBadge = '<span class="badge bg-warning text-dark">Pendente</span>';
            } else if (statusSolicitacao === 'APROVADA') {
                statusBadge = '<span class="badge bg-success">Aprovada</span>';
            } else if (statusSolicitacao === 'RECUSADA') {
                statusBadge = '<span class="badge bg-danger">Recusada</span>';
            } else if (statusSolicitacao === 'CANCELADA') {
                statusBadge = '<span class="badge bg-secondary">Cancelada</span>';
            } else {
                statusBadge = '<span class="badge bg-primary">Disponível</span>';
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
                                <a href="cadastro-produto.html?id=${produto.id_produto}" class="btn btn-primary w-50">Editar</a>
                                <button class="btn btn-outline-secondary w-50" onclick="excluirProduto(${produto.id_produto})">Excluir</button>
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

// Função para excluir produto (opcional)
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