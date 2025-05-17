document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('login-form').addEventListener('submit', async function (event) {
        event.preventDefault();

        const email = document.getElementById('email').value;
        const senha = document.getElementById('password').value;

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/usuario/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, senha })
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.setItem('access_token', result.access_token);
                localStorage.setItem('id_usuario', result.id_usuario);
                localStorage.setItem('nome_usuario', result.nome_usuario);
                alert('Login realizado com sucesso!');
                window.location.href = 'pages/pagina-inicial.html';
            } else {
                alert(result.msg || 'Email ou senha inválidos.');
            }
        } catch (error) {
            alert('Erro ao conectar ao servidor.');
        }
    });
});