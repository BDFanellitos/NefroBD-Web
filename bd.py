import sqlite3
import random
import string
import hashlib
import datetime
import os
import requests
import base64

# ==============================
# Configurações gerais
# ==============================
USE_MEMORY_DB = True
DB_FILE_PATH = "usuarios.db"

# Configuração para salvar no GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  
REPO = "https://github.com/BDFanellitos/Nefro_data"      
BRANCH = "main"                          

# ==============================
# Funções de conexão
# ==============================
def conectar_usuarios():
    if USE_MEMORY_DB:
        conn = sqlite3.connect(":memory:")
        carregar_dados_do_arquivo(conn)
        return conn
    else:
        return sqlite3.connect(DB_FILE_PATH)

def conectar_estoque(categoria):
    return sqlite3.connect(f"{categoria}_estoque.db")

def conectar_ponto():
    return sqlite3.connect("ponto.db")

# ==============================
# GitHub Sync
# ==============================
def commit_to_github(file_path=DB_FILE_PATH, message="Atualização de usuarios.db"):
    """Envia o arquivo atualizado para o GitHub"""
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN não encontrado. Skippando upload para o GitHub.")
        return False

    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"

    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")

    # Verifica se já existe no GitHub
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]

    data = {
        "message": message,
        "content": content,
        "branch": BRANCH,
    }
    if sha:
        data["sha"] = sha

    r = requests.put(url, json=data, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if r.status_code in (200, 201):
        print("✅ usuarios.db atualizado no GitHub com sucesso")
        return True
    else:
        print("❌ Erro ao atualizar no GitHub:", r.text)
        return False

# ==============================
# Operações com banco em memória
# ==============================
def carregar_dados_do_arquivo(conn_memory):
    if os.path.exists(DB_FILE_PATH):
        try:
            conn_file = sqlite3.connect(DB_FILE_PATH)
            conn_file.backup(conn_memory)
            conn_file.close()
            print(f"Dados carregados do arquivo {DB_FILE_PATH} para memória")
        except Exception as e:
            print(f"Erro ao carregar dados do arquivo: {e}")

def salvar_dados_no_arquivo(conn_memory):
    try:
        conn_file = sqlite3.connect(DB_FILE_PATH)
        conn_file.execute("DELETE FROM usuarios")
        conn_memory.backup(conn_file)
        conn_file.close()
        print(f"Dados salvos no arquivo {DB_FILE_PATH}")
        return True
    except Exception as e:
        print(f"Erro ao salvar dados no arquivo: {e}")
        return False

# ==============================
# Funções de manipulação de tabelas
# ==============================
def criar_tabela_usuarios():
    conn = conectar_usuarios()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    )
    """)
    if USE_MEMORY_DB:
        salvar_dados_no_arquivo(conn)
        commit_to_github(DB_FILE_PATH, "Estrutura inicial de usuarios.db criada")
    conn.close()

def criar_tabelas_estoque(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {categoria}_estoque (
        id TEXT PRIMARY KEY,
        item TEXT NOT NULL,
        infos TEXT,  
        quantidade REAL NOT NULL,
        data_modificacao TEXT NOT NULL,
        nome_usuario TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def criar_tabelas_anticorpos(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {categoria}_anticorpo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            nome TEXT NOT NULL,
            alvo TEXT NOT NULL,
            host TEXT NOT NULL,
            conjugado TEXT NOT NULL,
            marca TEXT NOT NULL,
            aliquotas REAL NOT NULL,
            vials REAL NOT NULL,
            data_modificacao TEXT NOT NULL,
            nome_usuario TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ==============================
# Funções auxiliares
# ==============================
def deletar_tabela(categoria):
    db_file = f"{categoria}_estoque.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        return f"Banco de dados '{db_file}' excluído com sucesso."
    else:
        return f"Banco de dados '{db_file}' não encontrado."

def listar_categorias():
    db_files = [f.replace("_estoque.db", "") for f in os.listdir() if f.endswith("_estoque.db")]
    return db_files

def gerar_id_unico():
    return "".join(random.choices(string.digits, k=6))

# ==============================
# Funções para usuarios.db
# ==============================
def cadastrar_usuario(username, email, senha):
    conn = conectar_usuarios()
    cursor = conn.cursor()
    user_id = gerar_id_unico()

    try:
        if not username or not email or not senha:
            return {"success": False, "error": "Todos os campos são obrigatórios"}

        cursor.execute(
            "INSERT INTO usuarios (id, username, email, senha) VALUES (?, ?, ?, ?)",
            (user_id, username, email, hash_senha(senha)),
        )
        conn.commit()

        if USE_MEMORY_DB:
            salvar_dados_no_arquivo(conn)
            commit_to_github(DB_FILE_PATH, "Novo usuário cadastrado")

        return {"success": True}

    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "username" in error_msg:
            return {"success": False, "error": "Nome de usuário já existe"}
        elif "email" in error_msg:
            return {"success": False, "error": "Email já cadastrado"}
        else:
            return {"success": False, "error": "Erro de integridade do banco de dados"}

    except Exception as e:
        return {"success": False, "error": f"Erro interno: {str(e)}"}

    finally:
        conn.close()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def autenticar_usuario(username, senha):
    if not username or not senha:
        return None
    conn = conectar_usuarios()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE username = ? AND senha = ?",
        (username, hash_senha(senha)),
    )
    user = cursor.fetchone()
    conn.close()
    return user

def sincronizar_usuarios():
    conn = conectar_usuarios()
    resultado = salvar_dados_no_arquivo(conn)
    if resultado:
        commit_to_github(DB_FILE_PATH, "Sincronização manual de usuarios.db")
    conn.close()
    return resultado

def redefinir_senha(email, nova_senha, key_phrase):
    key_phrase = "alohomora"
    conn = conectar_usuarios()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE usuarios SET senha = ? WHERE email = ?",
        (hash_senha(nova_senha), email),
    )
    conn.commit()
    if USE_MEMORY_DB:
        salvar_dados_no_arquivo(conn)
        commit_to_github(DB_FILE_PATH, "Senha redefinida")
    conn.close()

# ==============================
# Funções para estoque
# ==============================
def inserir_item_estoque(categoria, item, infos, quantidade, username):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    data_modificacao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item_id = gerar_id_unico()
    cursor.execute(
        f"INSERT INTO {categoria}_estoque (id, item, infos, quantidade, data_modificacao, nome_usuario) VALUES (?, ?, ?, ?, ?, ?)",
        (item_id, item, infos, quantidade, data_modificacao, username),
    )
    conn.commit()
    conn.close()

def inserir_item_anticorpo(categoria, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, username):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    data_modificacao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item_id = gerar_id_unico()
    cursor.execute(
        f"""
        INSERT INTO {categoria}_anticorpo (id, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, data_modificacao, nome_usuario) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (item_id, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, data_modificacao, username),
    )
    conn.commit()
    conn.close()

def deletar_item(categoria, item_id, tipo_tabela):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    if tipo_tabela == "estoque":
        cursor.execute(f"DELETE FROM {categoria}_estoque WHERE id = ?", (item_id,))
    elif tipo_tabela == "anticorpo":
        cursor.execute(f"DELETE FROM {categoria}_anticorpo WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def atualizar_estoque(categoria, item_id, coluna, nova_info):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    query = f"UPDATE {categoria}_estoque SET {coluna} = ? WHERE id = ?"
    cursor.execute(query, (nova_info, item_id))
    conn.commit()
    conn.close()

def atualizar_anticorpo(categoria, item_id, coluna, nova_info):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {categoria}_anticorpo SET {coluna} = ? WHERE id = ?", (nova_info, item_id))
    conn.commit()
    conn.close()

def listar_itens(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, item, infos, quantidade, data_modificacao, nome_usuario FROM {categoria}_estoque")
    itens = cursor.fetchall()
    conn.close()
    return itens

def listar_itens_anticorpo(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, data_modificacao, nome_usuario FROM {categoria}_anticorpo")
    itens = cursor.fetchall()
    conn.close()
    return itens

# ==============================
# Funções para ponto.db
# ==============================
def criar_tabela_ponto():
    conn = conectar_ponto()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ponto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_usuario TEXT NOT NULL,
        data TEXT NOT NULL,
        hora_entrada TEXT NOT NULL,
        hora_saida TEXT
    )
    """)
    conn.commit()
    conn.close()

def registrar_ponto(nome_usuario, data, hora_entrada, hora_saida=None):
    conn = conectar_ponto()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ponto (nome_usuario, data, hora_entrada, hora_saida) VALUES (?, ?, ?, ?)", (nome_usuario, data, hora_entrada, hora_saida))
    conn.commit()
    conn.close()

def obter_pontos_usuario(nome_usuario):
    conn = conectar_ponto()
    cursor = conn.cursor()
    cursor.execute("SELECT nome_usuario, data, hora_entrada, hora_saida FROM ponto WHERE nome_usuario = ?", (nome_usuario,))
    registros = cursor.fetchall()
    cursor.close()
    conn.close()
    return registros
