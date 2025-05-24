document.addEventListener('DOMContentLoaded', async () => {
    const nomeUsuario = localStorage.getItem('nome_usuario');
    if (nomeUsuario) {
        const spanBemVindo = document.getElementById('bem-vindo-usuario');
        if (spanBemVindo) {
            spanBemVindo.textContent = `Bem-vindo(a), ${nomeUsuario}`;
        }
    }

    // Carregar produtos ativos
    const token = localStorage.getItem('access_token');
    const productList = document.getElementById('product-list');
    if (!token || !productList) return;

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/produtos`, {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        const produtos = await response.json();

        if (!response.ok) {
            productList.innerHTML = `<div class="alert alert-danger">${produtos.msg || 'Erro ao carregar produtos.'}</div>`;
            return;
        }

        if (!produtos.length) {
            productList.innerHTML = '<div class="alert alert-info">Nenhum produto disponível no momento.</div>';
            return;
        }

        productList.innerHTML = '';
        // Função para normalizar categoria
        function normalizarCategoria(nome) {
            return nome
                .toLowerCase()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, ''); // remove acentos
        }

        produtos.forEach((produto, idx) => {
            // Imagens
            let imagensHtml = '';
            if (produto.imagens && produto.imagens.length > 0) {
                if (produto.imagens.length > 1) {
                    // Carrossel
                    const carouselId = `carouselProduto${produto.id_produto}`;
                    imagensHtml = `
                    <div id="${carouselId}" class="carousel slide" data-bs-ride="carousel">
                        <div class="carousel-inner">
                            ${produto.imagens.map((img, i) => `
                                <div class="carousel-item${i === 0 ? ' active' : ''}">
                                    <img src="${CONFIG.API_BASE_URL.replace('/api', '')}/${img.url_imagem}" class="d-block w-100 img-fluid" alt="Imagem do Produto" style="height: 200px; object-fit: cover;">
                                </div>
                            `).join('')}
                        </div>
                        <button class="carousel-control-prev" type="button" data-bs-target="#${carouselId}" data-bs-slide="prev">
                            <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                            <span class="visually-hidden">Anterior</span>
                        </button>
                        <button class="carousel-control-next" type="button" data-bs-target="#${carouselId}" data-bs-slide="next">
                            <span class="carousel-control-next-icon" aria-hidden="true"></span>
                            <span class="visually-hidden">Próximo</span>
                        </button>
                    </div>
                    `;
                } else {
                    imagensHtml = `<img src="${CONFIG.API_BASE_URL.replace('/api', '')}/${produto.imagens[0].url_imagem}" class="card-img-top img-fluid" alt="Produto" style="height: 200px; object-fit: cover;">`;
                }
            } else {
                imagensHtml = `<img src="../assets/placeholder.png" class="card-img-top img-fluid" alt="Produto" style="height: 200px; object-fit: cover;">`;
            }

            // Badge de categoria
            let categoriaBadge = '';
            let categoria = '';
            if (produto.categoria && produto.categoria.nome_categoria) {
                categoria = normalizarCategoria(produto.categoria.nome_categoria);
                let nomeCategoria = categoria === 'troca' ? 'Troca' : 'Doação';
                categoriaBadge = `<span class="badge bg-${categoria === 'troca' ? 'warning' : 'success'}">${nomeCategoria}</span>`;
            }

            // Link de negociação
            let linkNegociar = categoria === 'troca'
                ? `negociacao-troca.html?id=${produto.id_produto}`
                : `negociacao-doacao.html?id=${produto.id_produto}`;

            productList.innerHTML += `
                <div class="col-md-4" data-category="${categoria}">
                    <div class="card shadow">
                        ${imagensHtml}
                        <div class="card-body">
                            <h5 class="card-title">${produto.nome_produto}</h5>
                            <p class="card-text">${produto.descricao}</p>
                            ${categoriaBadge}
                            <a href="${linkNegociar}" class="btn btn-primary mt-2 w-100">Negociar</a>
                        </div>
                    </div>
                </div>
            `;
        });
    } catch (error) {
        productList.innerHTML = `<div class="alert alert-danger">Erro ao conectar ao servidor.</div>`;
    }
});

document.getElementById('search-name').addEventListener('input', function () {
    const searchValue = this.value.toLowerCase();
    const products = document.querySelectorAll('#product-list .col-md-4');
    products.forEach(product => {
        const title = product.querySelector('.card-title').textContent.toLowerCase();
        product.style.display = title.includes(searchValue) ? '' : 'none';
    });
});

document.getElementById('filter-category').addEventListener('change', function () {
    const filterValue = this.value;
    const products = document.querySelectorAll('#product-list .col-md-4');
    products.forEach(product => {
        const category = product.getAttribute('data-category');
        product.style.display = filterValue === '' || category === filterValue ? '' : 'none';
    });
});

document.querySelector('#logout').addEventListener('click', function () {
    localStorage.clear();
    window.location.href = '../index.html';
});