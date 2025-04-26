// Função para obter os parâmetros da URL
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        id: params.get('id'),
        name: params.get('name'),
        description: params.get('description'),
        image: params.get('image') // Novo parâmetro para a imagem
    };
}

// Preencher os dados do produto
document.addEventListener('DOMContentLoaded', () => {
    const { name, description, image } = getQueryParams();

    // Preencher os dados do produto
    document.getElementById('product-name').textContent = decodeURIComponent(name);
    document.getElementById('product-description').textContent = decodeURIComponent(description);

    // Preencher a imagem do produto
    if (image) {
        document.getElementById('product-image').src = decodeURIComponent(image);
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

// Função para finalizar a doação
function finalizeDonation() {
    alert('Doação finalizada com sucesso!');
    // Aqui você pode adicionar lógica para salvar a doação no banco de dados ou redirecionar o usuário
}