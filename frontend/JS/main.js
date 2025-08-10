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

/* NOVA TABELA POPUP*/
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
});

/* PONTO */
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

/* TABELA ANTICORPO */
document.addEventListener('DOMContentLoaded', () => {
        const table = document.getElementById('data-table');
        let editingTd = null;

        table.addEventListener('dblclick', (event) => {
        const target = event.target;
        if (target.tagName !== 'TD') return;
        if (editingTd) return; // Only one edit at a time

        // Prevent editing ID column (first column)
        if (target.cellIndex === 0) return;

        editingTd = target;
        const originalText = target.textContent;
        const field = target.getAttribute('data-field') || '';

        // Create input
        const input = document.createElement('input');
        input.type = 'text';
        input.value = originalText;
        input.className = 'table-edit-input bg-dracullaInputBg border border-dracullaInputBorder text-dracullaInputText px-1 text-[13px] leading-tight rounded-md w-full';
        input.style.height = '1.75rem'; // match row height approx
        target.textContent = '';
        target.appendChild(input);
        input.focus();
        input.select();

        // Save function
        function save() {
            const newValue = input.value.trim();
            if (newValue.length === 0) {
            target.textContent = originalText;
            } else {
            target.textContent = newValue;
            }
            editingTd = null;
        }

        // Cancel function
        function cancel() {
            target.textContent = originalText;
            editingTd = null;
        }

        input.addEventListener('blur', save);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
            e.preventDefault();
            save();
            } else if (e.key === 'Escape') {
            e.preventDefault();
            cancel();
            }
        });
        });
});

/*** RESET PASSWORDS **/
document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('passwordForm');
        const email = document.getElementById('email');
        const newPassword = document.getElementById('new-password');
        const confirmPassword = document.getElementById('confirm-password');
        const securityPhrase = document.getElementById('security-phrase');

        const emailError = document.getElementById('emailError');
        const passwordError = document.getElementById('passwordError');
        const phraseError = document.getElementById('phraseError');

        function validateEmail(email) {
        // Simple email regex validation
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
        }

        form.addEventListener('submit', (e) => {
        let valid = true;

        // Validate email
        if (!validateEmail(email.value.trim())) {
            emailError.classList.remove('hidden');
            valid = false;
            email.focus();
        } else {
            emailError.classList.add('hidden');
        }

        // Validate passwords match
        if (newPassword.value !== confirmPassword.value) {
            passwordError.classList.remove('hidden');
            if (valid) confirmPassword.focus();
            valid = false;
        } else {
            passwordError.classList.add('hidden');
        }

        // Validate security phrase (case insensitive)
        if (securityPhrase.value.trim().toLowerCase() !== 'alohomora') {
            phraseError.classList.remove('hidden');
            if (valid) securityPhrase.focus();
            valid = false;
        } else {
            phraseError.classList.add('hidden');
        }

        if (!valid) {
            e.preventDefault();
        }
        });

        // Hide errors on input
        email.addEventListener('input', () => {
        if (!emailError.classList.contains('hidden')) {
            emailError.classList.add('hidden');
        }
        });
        newPassword.addEventListener('input', () => {
        if (!passwordError.classList.contains('hidden')) {
            passwordError.classList.add('hidden');
        }
        });
        confirmPassword.addEventListener('input', () => {
        if (!passwordError.classList.contains('hidden')) {
            passwordError.classList.add('hidden');
        }
        });
        securityPhrase.addEventListener('input', () => {
        if (!phraseError.classList.contains('hidden')) {
            phraseError.classList.add('hidden');
        }
        });
});


/*** FRASES */
document.addEventListener('DOMContentLoaded', () => {
const frases = [
    "Onde a ciência encontra a organização… e o café mantém tudo funcionando.",
    "Eu juro solenemente atualizar o banco de dados ✋",
    "Cada dado armazenado é um passo para a próxima descoberta (e para a saúde mental).",
    "Organizar hoje para publicar amanhã.",
    "Ciência sem organização é só uma bagunça sofisticada.",
    "Será que tem amostra? Mantenha o BD atualizado e você irá saber!",
    "Levante a mão todo mundo que odeia fazer almoxarifado ✋",
    "Se não atualizar o estoque, o reagente some, e a culpa é sua 👉",
    "Se o estoque fosse um experimento, atualizar seria o controle positivo!",
    "Se você não quer congelar no freezer, melhor atualizar o estoque!",
    "Reagente em falta? Culpa do estoque preguiçoso (ou do último que esqueceu de atualizar)."
    ];

    // Escolhe uma frase aleatória
    const fraseAleatoria = frases[Math.floor(Math.random() * frases.length)];

    // Função para simular digitação
    function escreverTexto(elemento, texto, delay = 50) {
    let i = 0;
    function digitar() {
        if (i < texto.length) {
        elemento.textContent += texto.charAt(i);
        i++;
        setTimeout(digitar, delay);
        }
    }
    digitar();
    }

// Executa
const elementoFrase = document.getElementsByClassName("typewriter")[0];
escreverTexto(elementoFrase, fraseAleatoria, 50); // 50ms por letra
});
