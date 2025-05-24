document.getElementById('cep').addEventListener('blur', function () {
    const cep = this.value.replace(/\D/g, '');
    if (cep.length === 8) {
        fetch(`https://viacep.com.br/ws/${cep}/json/`)
            .then(response => response.json())
            .then(data => {
                if (!data.erro) {
                    document.getElementById('bairro').value = data.bairro;
                    document.getElementById('rua').value = data.logradouro;
                    document.getElementById('cidade').value = data.localidade;
                    document.getElementById('estado').value = data.uf;
                } else {
                    alert('CEP não encontrado.');
                }
            })
            .catch(() => alert('Erro ao buscar o CEP.'));
    } else {
        alert('CEP inválido.');
    }
});

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('cadastro-form').addEventListener('submit', async function (event) {
        event.preventDefault();

        // Captura os valores dos campos
        const data = {
            nome_usuario: document.getElementById('name').value,
            cpf: document.getElementById('cpf').value,
            telefone: document.getElementById('phone').value,
            email: document.getElementById('email').value,
            senha: document.getElementById('password').value,
            data_nascimento: document.getElementById('birthdate').value,
            cep: document.getElementById('cep').value,
            bairro: document.getElementById('bairro').value,
            rua: document.getElementById('rua').value,
            numero: document.getElementById('numero').value,
            complemento: document.getElementById('complemento').value,
            cidade: document.getElementById('cidade').value,
            estado: document.getElementById('estado').value
        };

        // Validação de senha
        const confirmSenha = document.getElementById('confirm-password').value;
        if (data.senha !== confirmSenha) {
            alert('As senhas não coincidem!');
            return;
        }

        try {
            // Envia os dados para o backend
            const response = await fetch(`${CONFIG.API_BASE_URL}/usuario/cadastro`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                alert(result.msg);
                window.location.href = '../index.html'; // Redireciona após o cadastro
            } else {
                alert(result.msg || 'Erro ao cadastrar usuário.');
            }
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro ao conectar ao servidor.');
        }
    });
});

