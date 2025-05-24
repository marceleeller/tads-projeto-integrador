// Função para obter o id do produto da URL
function getProductIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

// Preencher os campos do formulário com dados do produto (edição)
document.addEventListener('DOMContentLoaded', async () => {
    const productId = getProductIdFromUrl();

    // Troca o texto do botão se for edição
    const submitBtn = document.querySelector('#cadastro-produto-form button[type="submit"]');
    if (productId && submitBtn) {
        submitBtn.textContent = 'Editar Produto';
    }

    // --- EDIÇÃO (preencher campos se for edição) ---
    if (productId) {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${CONFIG.API_BASE_URL}/produto/${productId}`, {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            });
            if (response.ok) {
                const produto = await response.json();
                console.log(produto);
                document.getElementById('product-name').value = produto.nome_produto || '';
                document.getElementById('description').value = produto.descricao || '';
                document.getElementById('quantity').value = produto.quantidade || 1;
                if (produto.status === 'NOVO') {
                    document.getElementById('status-novo').checked = true;
                } else if (produto.status === 'USADO') {
                    document.getElementById('status-usado').checked = true;
                }
                if (produto.categoria && produto.categoria.id_categoria) {
                    const catRadio = document.querySelector(`input[name="category"][value="${produto.categoria.id_categoria}"]`);
                    if (catRadio) catRadio.checked = true;
                }
                // Preencher imagens existentes se desejar
                if (produto.imagens && produto.imagens.length > 0) {
                    const previewContainer = document.getElementById('image-preview');
                    if (previewContainer) {
                        previewContainer.innerHTML = '';
                        produto.imagens.forEach(imagem => {
                            const img = document.createElement('img');
                            // Use o mesmo padrão de URL das outras telas
                            img.src = `${CONFIG.API_BASE_URL.replace('/api', '')}/${imagem.url_imagem}`;
                            img.alt = imagem.url_imagem;
                            img.style.maxWidth = '100px';
                            img.style.maxHeight = '100px';
                            img.classList.add('img-thumbnail', 'me-2', 'mb-2');
                            previewContainer.appendChild(img);
                        });
                    }
                }
            } else {
                alert('Erro ao buscar dados do produto.');
            }
        } catch (error) {
            alert('Erro ao conectar ao servidor.');
        }
    }

    // --- CADASTRO ---
    const form = document.getElementById('cadastro-produto-form');
    if (form) {
        form.addEventListener('submit', async function (event) {
            event.preventDefault();

            const nome_produto = document.getElementById('product-name').value;
            const descricao = document.getElementById('description').value;
            const quantidade = document.getElementById('quantity').value;
            const status = document.querySelector('input[name="status-produto"]:checked')?.value;
            const id_categoria = document.querySelector('input[name="category"]:checked')?.value;

            if (!id_categoria) {
                alert('Selecione seu interesse.');
                return;
            }

            if (!status) {
                alert('Selecione o estado do produto.');
                return;
            }

            const imagensInput = document.getElementById('images');
            const token = localStorage.getItem('access_token');
            if (!token) {
                alert('Você precisa estar logado para cadastrar um produto.');
                return;
            }

            try {
                let response, result;
                if (productId) {
                    // PUT - Alterar produto
                    const data = {
                        nome_produto,
                        descricao,
                        quantidade,
                        status,
                        id_categoria
                    };
                    response = await fetch(`${CONFIG.API_BASE_URL}/produto/${productId}`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': 'Bearer ' + token,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    });
                } else {
                    // POST - Cadastrar produto
                    const formData = new FormData();
                    formData.append('nome_produto', nome_produto);
                    formData.append('descricao', descricao);
                    formData.append('quantidade', quantidade);
                    formData.append('status', status);
                    formData.append('id_categoria', id_categoria);

                    if (imagensInput && imagensInput.files.length > 0) {
                        for (let i = 0; i < imagensInput.files.length; i++) {
                            formData.append('images', imagensInput.files[i]);
                        }
                    }

                    response = await fetch(`${CONFIG.API_BASE_URL}/produto`, {
                        method: 'POST',
                        headers: {
                            'Authorization': 'Bearer ' + token
                        },
                        body: formData
                    });
                }

                result = await response.json();

                if (response.ok) {
                    alert(productId ? 'Produto alterado com sucesso!' : 'Produto cadastrado com sucesso!');
                    window.location.href = 'meus-produtos.html';
                } else {
                    alert(result.msg || 'Erro ao salvar produto.');
                }
            } catch (error) {
                alert('Erro ao conectar ao servidor.');
            }
        });
    }

    // --- PRÉ-VISUALIZAÇÃO DAS IMAGENS ---
    const imagensInput = document.getElementById('images');
    if (imagensInput) {
        imagensInput.addEventListener('change', function () {
            const previewContainer = document.getElementById('image-preview');
            if (previewContainer) {
                previewContainer.innerHTML = '';
                const files = Array.from(this.files);
                files.forEach(file => {
                    if (file.type.startsWith('image/')) {
                        const reader = new FileReader();
                        reader.onload = function (e) {
                            const img = document.createElement('img');
                            img.src = e.target.result;
                            img.alt = file.name;
                            img.style.maxWidth = '100px';
                            img.style.maxHeight = '100px';
                            img.classList.add('img-thumbnail');
                            previewContainer.appendChild(img);
                        };
                        reader.readAsDataURL(file);
                    }
                });
            }
        });
    }

    document.querySelector('#logout').addEventListener('click', function () {
        localStorage.clear();
        window.location.href = '../index.html';
    });
});