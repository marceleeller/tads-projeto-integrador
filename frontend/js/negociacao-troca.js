// Função para obter os parâmetros da URL
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        id: params.get('id'),
        name: params.get('name'),
        description: params.get('description'),
        category: params.get('category'),
        isOwner: params.get('isOwner') === 'true' // Verifica se o usuário é o dono
    };
}

// Preencher os dados do produto e exibir a interface de troca se necessário
document.addEventListener('DOMContentLoaded', () => {
    const { name, description, category, isOwner } = getQueryParams();

    // Preencher os dados do produto
    document.getElementById('product-name').textContent = decodeURIComponent(name);
    document.getElementById('product-description').textContent = decodeURIComponent(description);
    const categoryBadge = document.getElementById('product-category');
    categoryBadge.textContent = category === 'troca' ? 'Troca' : 'Doação';
    categoryBadge.className = category === 'troca' ? 'badge bg-warning' : 'badge bg-success';

    // Exibir a interface de adicionar produtos se o usuário não for o dono
    if (!isOwner && category === 'troca') {
        document.getElementById('add-products-interface').style.display = 'block';
    }
});

// Função para enviar mensagens no chat
function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (message) {
        const chatMessages = document.getElementById('chat-messages');
        const newMessage = document.createElement('div');
        newMessage.classList.add('text-end', 'mb-2');
        newMessage.innerHTML = `<span class="badge bg-primary">Você:</span> <span>${message}</span>`;
        chatMessages.appendChild(newMessage);
        input.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Função para adicionar produtos à caixinha de troca como cards
function addToMyTradeBox(productName, productDescription) {
    const tradeBox = document.getElementById('my-trade-box');

    // Criar o card do produto
    const col = document.createElement('div');
    col.classList.add('col-md-4');

    const card = document.createElement('div');
    card.classList.add('card', 'shadow');

    const img = document.createElement('img');
    img.src = '../assets/placeholder.png'; // Substitua pelo caminho real da imagem
    img.alt = productName;
    img.classList.add('card-img-top', 'img-fluid');
    img.style.height = '150px';
    img.style.objectFit = 'cover';

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body', 'text-center');

    const title = document.createElement('h6');
    title.classList.add('card-title');
    title.textContent = productName;

    const description = document.createElement('p');
    description.classList.add('card-text', 'text-muted');
    description.textContent = productDescription;

    const removeButton = document.createElement('button');
    removeButton.classList.add('btn', 'btn-sm', 'btn-danger', 'mt-2');
    removeButton.textContent = 'Remover';
    removeButton.onclick = () => col.remove();

    // Montar o card
    cardBody.appendChild(title);
    cardBody.appendChild(description);
    cardBody.appendChild(removeButton);
    card.appendChild(img);
    card.appendChild(cardBody);
    col.appendChild(card);

    // Adicionar o card ao container
    tradeBox.appendChild(col);
}

// Função para finalizar a troca
function finalizeTrade() {
    alert('Troca finalizada com sucesso!');
    // Aqui você pode adicionar lógica para salvar a troca no banco de dados ou redirecionar o usuário
}

document.querySelector('#logout').addEventListener('click', function () {
    localStorage.clear();
    window.location.href = '../index.html';
});