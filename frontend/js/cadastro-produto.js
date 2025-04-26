// Função para obter os parâmetros da URL
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        id: params.get('id'),
        name: params.get('name'),
        description: params.get('description'),
        category: params.get('category')
    };
}

// Preencher os campos do formulário
document.addEventListener('DOMContentLoaded', () => {
    const { name, description, category } = getQueryParams();

    if (name) document.getElementById('product-name').value = decodeURIComponent(name);
    if (description) document.getElementById('description').value = decodeURIComponent(description);
    if (category) {
        document.getElementById(category).checked = true;
    }
});

// Função para pré-visualizar as imagens selecionadas
document.getElementById('images').addEventListener('change', function () {
    const previewContainer = document.getElementById('image-preview');
    previewContainer.innerHTML = ''; // Limpa a pré-visualização anterior

    const files = Array.from(this.files); // Obtém os arquivos selecionados
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
});