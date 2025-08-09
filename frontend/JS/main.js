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

/* NOVA TABELA E CARREGAR TABELAS*/
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
});

/* PONTO */
// --- PONTO (versão compatível com seu HTML) ---
document.addEventListener('DOMContentLoaded', () => {
    const openPopupBtn = document.getElementById('ponto_btn');
    const popup = document.getElementById('popup_novo_ponto');
    const closePopupBtn = document.getElementById('closePopupBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const form = document.getElementById('registerPointForm');
    const usernameInput = document.getElementById('username');
    const dateInput = document.getElementById('date');
    const arrivalInput = document.getElementById('arrivalTime');
    const departureInput = document.getElementById('departureTime');
    const exportBtn = document.getElementById('exportBtn');

    if (!popup) {
        console.error('Elemento registerPointPopup não encontrado no DOM.');
        return;
    }

    // Helper: define max date = hoje
    function setMaxDate() {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, "0");
        const dd = String(today.getDate()).padStart(2, "0");
        const maxDate = `${yyyy}-${mm}-${dd}`;
        if (dateInput) {
        dateInput.setAttribute("max", maxDate);
        dateInput.value = maxDate;
        }
    }

    // Focus trap variables
    let previousActiveElement = null;
    let trapHandler = null;

    function trapFocus(element) {
        const focusableSelector =
        'a[href], area[href], input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), iframe, object, embed, [tabindex]:not([tabindex="-1"])';
        const focusable = Array.from(element.querySelectorAll(focusableSelector)).filter(el => el.offsetParent !== null);
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        previousActiveElement = document.activeElement;
        first.focus();

        trapHandler = function (e) {
        if (e.key === 'Tab') {
            if (e.shiftKey) { // shift + tab
            if (document.activeElement === first) {
                e.preventDefault();
                last.focus();
            }
            } else { // tab
            if (document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
            }
        } else if (e.key === 'Escape') {
            closePopup();
        }
        };

        element.addEventListener('keydown', trapHandler);
    }

    function removeTrap() {
        if (trapHandler) {
        popup.removeEventListener('keydown', trapHandler);
        trapHandler = null;
        }
        if (previousActiveElement && typeof previousActiveElement.focus === 'function') {
        previousActiveElement.focus();
        }
        previousActiveElement = null;
    }

    // Abrir popup
    if (openPopupBtn) {
        openPopupBtn.addEventListener('click', () => {
        const user = localStorage.getItem('usuario');
        if (!user) {
            alert('Usuário não está logado!');
            return;
        }

        if (usernameInput) usernameInput.value = user;
        setMaxDate();
        popup.classList.remove('hidden');

        // foco e acessibilidade
        if (dateInput) dateInput.focus();
        trapFocus(popup);
        });
    } else {
        console.warn('openPopupBtn não encontrado no DOM.');
    }

    // Fechar popup
    function closePopup() {
        popup.classList.add('hidden');
        if (form) form.reset();
        removeTrap();
    }

    if (closePopupBtn) closePopupBtn.addEventListener('click', closePopup);
    if (cancelBtn) cancelBtn.addEventListener('click', closePopup);

    // fechar no ESC (redundante com trap, mas seguro)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !popup.classList.contains('hidden')) {
        closePopup();
        }
    });

    // util: converte "HH:MM" -> minutos
    function timeToMinutes(t) {
        if (!t) return null;
        const parts = t.split(':');
        if (parts.length < 2) return null;
        return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
    }

    // Submissão do formulário -> envia para backend
    if (form) {
        form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const usuario = usernameInput ? usernameInput.value : localStorage.getItem('usuario');
        const data = dateInput ? dateInput.value : '';
        const entrada = arrivalInput ? arrivalInput.value : '';
        const saida = departureInput ? departureInput.value : '';

        if (!usuario) {
            alert('Usuário não está logado.');
            return;
        }
        if (!data || !entrada) {
            alert('Preencha ao menos a data e o horário de entrada.');
            return;
        }

        // valida data não futura
        const selectedDate = new Date(data);
        selectedDate.setHours(0, 0, 0, 0);
        const hoje = new Date();
        hoje.setHours(0, 0, 0, 0);
        if (selectedDate > hoje) {
            alert('A data selecionada não pode ser no futuro.');
            return;
        }

        // valida horas (se saida estiver preenchida)
        const entradaMin = timeToMinutes(entrada);
        const saidaMin = timeToMinutes(saida);
        if (entradaMin === null) {
            alert('Horário de chegada inválido.');
            return;
        }
        if (saida && saidaMin !== null && entradaMin > saidaMin) {
            alert('A hora de chegada não pode ser maior que a hora de saída.');
            arrivalInput.focus();
            return;
        }

        // envia para backend
        try {
            const res = await fetch(`${BASE_URL}/api/ponto`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                usuario,
                data,
                entrada,
                saida: saida || null
            })
            });

            let json;
            try { json = await res.json(); } catch (err) { json = null; }

            if (res.ok && json && json.status === 'success') {
            alert('Ponto registrado com sucesso!');
            closePopup();
            } else {
            const msg = (json && json.message) ? json.message : `Erro ao registrar ponto (status ${res.status}).`;
            alert(msg);
            }
        } catch (error) {
            alert('Erro na conexão com o servidor: ' + error);
        }
        });
    } else {
        console.warn('Form registerPointForm não encontrado.');
    }

    // Exportar ponto -> chama rota /api/exportar_ponto e faz download do CSV
    if (exportBtn) {
        exportBtn.addEventListener('click', async () => {
        const usuario = usernameInput ? usernameInput.value || localStorage.getItem('usuario') : localStorage.getItem('usuario');
        if (!usuario) {
            alert('Usuário não está logado.');
            return;
        }

        try {
            const res = await fetch(`${BASE_URL}/api/exportar_ponto?usuario=${encodeURIComponent(usuario)}`);
            if (!res.ok) {
            const text = await res.text().catch(() => '');
            alert('Erro ao exportar ponto: ' + (text || res.status));
            return;
            }

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            // backend devolve CSV; o Excel abre CSV sem problema
            link.download = `ponto_${usuario}.csv`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            alert('Erro na conexão com o servidor: ' + error);
        }
        });
    } else {
        console.warn('Botão exportBtn não encontrado.');
    }

}); 

