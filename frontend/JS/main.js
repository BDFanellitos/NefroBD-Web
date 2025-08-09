const BASE_URL = window.location.hostname.includes('localhost')
    ? 'http://localhost:5500'
    : 'https://nefrobd-web.onrender.com';

// Função de fetch com timeout
async function fetchWithTimeout(resource, options = {}, timeout = 15000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(resource, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        throw error;
    }
}

window.addEventListener("DOMContentLoaded", () => {
    console.log("JS carregado");

    /* LOGIN */
    const form = document.getElementById('login_form');
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault(); 

            const username = document.getElementById('username_login').value;
            const senha = document.getElementById('username_password').value;

            // Exibe loading
            const loadingMsg = document.createElement('div');
            loadingMsg.textContent = "Conectando ao servidor...";
            loadingMsg.style.color = "blue";
            document.body.appendChild(loadingMsg);

            try {
                const res = await fetchWithTimeout(`${BASE_URL}/api/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, senha })
                });

                const data = await res.json();

                if (res.ok && data.status === 'success') {
                    alert('Login bem-sucedido! Bem-vindo, ' + data.user);
                    localStorage.setItem('usuario', data.user);
                    window.location.href = 'https://bdfanellitos.github.io/NefroBD-Web/frontend/home.html'; 
                } else {
                    alert(data.message || 'Erro ao fazer login');
                }
            } catch (error) {
                if (error.name === 'AbortError') {
                    alert('Tempo limite excedido. O servidor pode estar hibernando, tente novamente em alguns segundos.');
                } else {
                    alert('Erro de conexão com o servidor: ' + error);
                }
            } finally {
                loadingMsg.remove();
            }
        });
    }
});

/* CADASTRO */
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('sign_up_form');
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
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
                const res = await fetchWithTimeout(`${BASE_URL}/api/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, senha })
                });

                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    alert('Usuário cadastrado com sucesso!');
                    window.location.href = './index.html';
                } else {
                    alert(data.message || 'Erro ao cadastrar usuário.');
                }
            } catch (error) {
                if (error.name === 'AbortError') {
                    alert('Tempo limite excedido. O servidor pode estar hibernando.');
                } else {
                    alert('Erro na requisição: ' + error);
                }
            }
        });
    }
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
            const res = await fetchWithTimeout(`${BASE_URL}/api/criar_tabela`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome, tipo })
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
            if (error.name === 'AbortError') {
                alert('Tempo limite excedido. Tente novamente.');
            } else {
                alert('Erro ao se comunicar com o servidor: ' + error);
            }
        }
    };

    async function carregarTabelas() {
        try {
            listaTabelas.innerHTML = "<p style='color:blue'>Carregando tabelas...</p>";

            const res = await fetchWithTimeout(`${BASE_URL}/api/categorias`);
            const data = await res.json();

            listaTabelas.innerHTML = '';

            if (!data.tabelas || data.tabelas.length === 0) {
                listaTabelas.innerHTML = "<p>Nenhuma tabela encontrada.</p>";
                return;
            }

            data.tabelas.forEach(tabela => {
                const btn = document.createElement('button');
                btn.textContent = tabela.table_name;
                btn.className = "bg-[#6170A0] text-white font-semibold py-14 rounded-md shadow-md text-sm";
                btn.type = "button";
                listaTabelas.appendChild(btn);
            });
        } catch (error) {
            if (error.name === 'AbortError') {
                listaTabelas.innerHTML = "<p style='color:red'>Servidor demorou para responder. Tente novamente.</p>";
            } else {
                listaTabelas.innerHTML = "<p style='color:red'>Erro ao carregar tabelas.</p>";
                console.error(error);
            }
        }
    }

    carregarTabelas();

/* PONTO */    
    async function registrarPonto() {
        const usuario = document.getElementById('ponto_usuario').value;
        const data = document.getElementById('ponto_data').value;
        const entrada = document.getElementById('ponto_entrada').value;
        const saida = document.getElementById('ponto_saida').value;

        if (!usuario) {
            alert('Usuário não está logado!');
            return;
        }
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
    }

    // Função para fechar popup
    function fecharPopupPonto() {
        const popup = document.getElementById('popup_ponto');
        popup.classList.add('hidden');
        document.getElementById('ponto_entrada').value = '';
        document.getElementById('ponto_saida').value = '';
    }

});
