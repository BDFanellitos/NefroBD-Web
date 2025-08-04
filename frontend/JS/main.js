const BASE_URL = window.location.hostname.includes('localhost')
  ? 'http://localhost:5000'
  : 'https://nefrobd-web.onrender.com';


window.addEventListener("DOMContentLoaded", () => {
    console.log("JS carregado");

    /* LOGIN */
    const form = document.getElementById('login_form');

    form.addEventListener('submit', async function (e) {
        e.preventDefault(); // Impede o envio padrão

        const username = document.getElementById('username_login').value;
        const senha = document.getElementById('username_password').value;

        try {
            const res = await fetch(`${BASE_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, senha })
            });
            console.log(res);


            const data = await res.json();

            if (res.ok && data.status === 'success') {
                alert('Login bem-sucedido! Bem-vindo, ' + data.user);
                localStorage.setItem('usuario', data.user);
                window.location.href = 'https://bdfanellitos.github.io/NefroBD-Web/frontend/home.html'; 
            } else {
                alert(data.message || 'Erro ao fazer login');
            }
        } catch (error) {
            alert('Erro de conexão com o servidor: ' + error);
        }
    });
})

 /* CADASTRO */
document.addEventListener('DOMContentLoaded', () => {
    console.log("Cadastro JS carregado");

    const form = document.getElementById('sign_up_form');
    form.addEventListener('submit', async function (e) {
        e.preventDefault(); // Impede envio tradicional
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const senha = document.getElementById('password').value;
        const confirmarSenha = document.getElementById('confirm-password').value;

        if (!username || !email || !senha || !confirmarSenha) {
        alert('Por favor, preencha todos os campos.');
        return;
        }

        if (senha !== confirmarSenha) {
        alert('As senhas não conferem.');
        return;
        }

        try {
            const res = await fetch(`${BASE_URL}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, senha })
            });

        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
            alert('Usuário cadastrado com sucesso!');
            window.location.href = './index.html'; // Login page
        } else {
            alert(data.message || 'Erro ao cadastrar usuário.');
        }

        } catch (error) {
        alert('Erro na requisição: ' + error);
        }
    });
});

/* NOVA TABELA */
document.addEventListener("DOMContentLoaded", () => {
    const popup = document.getElementById('popup_nova_tabela');
    const listaTabelas = document.getElementById('lista_tabelas');

    const novaTabelaBtn = document.getElementById('nova_tabela_btn');
    if (novaTabelaBtn) {
        novaTabelaBtn.addEventListener('click', () => {
        popup.classList.remove('hidden');
        });
    }

    window.fecharPopup = function () {
        popup.classList.add('hidden');
        document.getElementById('nome_tabela').value = '';
    };

    window.criarTabela = async function () {
        const nome = document.getElementById('nome_tabela').value.trim();
        const tipo = document.querySelector('input[name="tipo_tabela"]:checked').value;

        if (!nome) {
        alert('Por favor, insira o nome da tabela.');
        return;
        }

        try {
            const res = await fetch(`${BASE_URL}/api/criar_tabela`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, tipo })
            });

        });

        const data = await res.json();

        if (res.ok && data.status === 'success') {
            alert('Tabela criada com sucesso!');
            fecharPopup();
            carregarTabelas();
        } else {
            alert(data.message || 'Erro ao criar tabela.');
        }
        } catch (error) {
        alert('Erro ao se comunicar com o servidor: ' + error);
        }
    };

    async function carregarTabelas() {
        try {
        const res = await fetch(`${BASE_URL}/api/categorias`);
        const data = await res.json();

        listaTabelas.innerHTML = '';

        data.tabelas?.forEach(tabela => {
            const btn = document.createElement('button');
            btn.textContent = tabela.table_name;
            btn.className = "bg-[#6170A0] text-white font-semibold py-14 rounded-md shadow-md text-sm";
            btn.type = "button";
            listaTabelas.appendChild(btn);
        });
        } catch (error) {
        console.error('Erro ao carregar tabelas:', error);
        }
    }

    carregarTabelas(); // chama logo após carregar
});


document.addEventListener('DOMContentLoaded', () => {
    const popupPonto = document.getElementById('popup_ponto');

    // Ativa botão de abrir popup
    const btnPonto = document.getElementById('btn_ponto');
    if (btnPonto) {
        btnPonto.addEventListener('click', () => {
        const user = localStorage.getItem('usuario');
        if (!user) {
            alert('Usuário não está logado!');
            return;
        }

        document.getElementById('ponto_usuario').value = user;

        // Preenche a data de hoje e define limite máximo
        const hoje = new Date().toISOString().split("T")[0];
        document.getElementById('ponto_data').value = hoje;
        document.getElementById('ponto_data').max = hoje;

        popupPonto.classList.remove('hidden');
        });
    }

    // Fecha popup
    window.fecharPopupPonto = function () {
        popupPonto.classList.add('hidden');
        document.getElementById('ponto_entrada').value = '';
        document.getElementById('ponto_saida').value = '';
    };

    // Envia dados para o backend
    window.registrarPonto = async function () {
        const usuario = document.getElementById('ponto_usuario').value;
        const data = document.getElementById('ponto_data').value;
        const entrada = document.getElementById('ponto_entrada').value;
        const saida = document.getElementById('ponto_saida').value;

        if (!data || !entrada) {
        alert('Preencha ao menos a data e o horário de entrada.');
        return;
        }

        const hoje = new Date().toISOString().split("T")[0];
        if (data > hoje) {
        alert('Não é permitido registrar ponto para datas futuras.');
        return;
        }

        try {
            const res = await fetch(`${BASE_URL}/api/ponto`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario, data, entrada, saida })
            });

        });

        const response = await res.json();

        if (res.ok && response.status === 'success') {
            alert('Ponto registrado com sucesso!');
            fecharPopupPonto();
        } else {
            alert(response.message || 'Erro ao registrar ponto.');
        }
        } catch (error) {
        alert('Erro na conexão com o servidor: ' + error);
        }
    };

    // Exporta os dados
    window.exportarPonto = async function () {
    const usuario = document.getElementById('ponto_usuario').value;

    try {
        const res = await fetch(`${BASE_URL}/api/exportar_ponto?usuario=${encodeURIComponent(usuario)}`);
        if (!res.ok) {
        throw new Error('Erro ao exportar ponto.');
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');

        link.href = url;
        link.download = `ponto_${usuario}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        alert('Erro ao exportar ponto: ' + error);
    }
    };


});

