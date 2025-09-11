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
DB_FILE_PATH = "usuarios.db"
PONTO_DB_FILE = "ponto.db"

DEPLOY = os.getenv("DEPLOY") == "1"  
USE_MEMORY_DB = not DEPLOY           
USE_MEMORY_PONTO = not DEPLOY       



# Configuração para salvar no GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  
REPO = "BDFanellitos/Nefro_data"    
BRANCH = "main"                          

# ==============================
# Funções de conexão
# ==============================
def conectar_usuarios():
    if USE_MEMORY_DB:
        conn = sqlite3.connect(":memory:")
        carregar_dados_usuarios_do_arquivo(conn)  
        return conn
    else:
        return sqlite3.connect(DB_FILE_PATH)

def conectar_estoque(categoria):
    return sqlite3.connect(f"{categoria}_estoque.db")

def conectar_ponto():
    if USE_MEMORY_PONTO:
        conn = sqlite3.connect(":memory:")
        carregar_dados_ponto_do_arquivo(conn)  
        return conn
    else:
        return sqlite3.connect(PONTO_DB_FILE)

# ==============================
# GitHub Sync
# ==============================
def commit_to_github(file_path, message):
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN não encontrado. Skippando upload para o GitHub.")
        return False

    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")

    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = r.json()["sha"] if r.status_code == 200 else None

    data = {"message": message, "content": content, "branch": BRANCH}
    if sha:
        data["sha"] = sha

    r = requests.put(url, json=data, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if r.status_code in (200, 201):
        print(f"✅ {file_path} atualizado no GitHub")
        return True
    else:
        print(f"❌ Erro ao atualizar {file_path} no GitHub:", r.text)
        return False
    

# ==============================
# Operações com banco em memória
# ==============================
def carregar_dados_usuarios_do_arquivo(conn_memory):
    if os.path.exists(DB_FILE_PATH):
        conn_file = sqlite3.connect(DB_FILE_PATH)
        conn_file.backup(conn_memory)
        conn_file.close()

def salvar_dados_usuarios_no_arquivo(conn_memory):
    try:
        conn_file = sqlite3.connect(DB_FILE_PATH)
        cursor_file = conn_file.cursor()
        cursor_file.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            )
        """)
        conn_memory.backup(conn_file)
        conn_file.close()
        return True  # ✅ retorna True se deu certo
    except Exception as e:
        print(f"Erro ao salvar usuarios.db: {e}")
        return False

def carregar_dados_ponto_do_arquivo(conn_memory):
    if os.path.exists(PONTO_DB_FILE):
        conn_file = sqlite3.connect(PONTO_DB_FILE)
        conn_file.backup(conn_memory)
        conn_file.close()

def salvar_dados_ponto_no_arquivo(conn_memory):
    try:
        conn_file = sqlite3.connect(PONTO_DB_FILE)
        cursor_file = conn_file.cursor()
        cursor_file.execute("""
            CREATE TABLE IF NOT EXISTS ponto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_usuario TEXT NOT NULL,
                data TEXT NOT NULL,
                hora_entrada TEXT NOT NULL,
                hora_saida TEXT
            )
        """)
        conn_memory.backup(conn_file)
        conn_file.close()
        return True  # ✅ retorna True se deu certo
    except Exception as e:
        print(f"Erro ao salvar ponto.db: {e}")
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
    conn.commit()
    if USE_MEMORY_DB:
        salvar_dados_usuarios_no_arquivo(conn)
        commit_to_github(DB_FILE_PATH, "Tabela usuarios criada")
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
    cursor.execute(
        "INSERT INTO usuarios (id, username, email, senha) VALUES (?, ?, ?, ?)",
        (user_id, username, email, hash_senha(senha))
    )
    conn.commit()
    if USE_MEMORY_DB:
        salvar_dados_usuarios_no_arquivo(conn)
        commit_to_github(DB_FILE_PATH, f"Novo usuário {username}")
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
    resultado = salvar_dados_usuarios_no_arquivo(conn) 
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
        salvar_dados_usuarios_no_arquivo(conn)
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
    if USE_MEMORY_PONTO:
        salvar_dados_ponto_no_arquivo(conn)
        commit_to_github(PONTO_DB_FILE, "Tabela ponto criada")
    conn.close()

def registrar_ponto(nome_usuario, data, hora_entrada, hora_saida=None):
    conn = conectar_ponto()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ponto (nome_usuario, data, hora_entrada, hora_saida) VALUES (?, ?, ?, ?)",
        (nome_usuario, data, hora_entrada, hora_saida)
    )
    conn.commit()
    if USE_MEMORY_PONTO:
        salvar_dados_ponto_no_arquivo(conn)
        commit_to_github(PONTO_DB_FILE, "Novo registro de ponto")  # opcional
    conn.close()

def obter_pontos_usuario(nome_usuario):
    conn = conectar_ponto()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome_usuario, data, hora_entrada, hora_saida FROM ponto WHERE nome_usuario = ?",
        (nome_usuario,)
    )
    registros = cursor.fetchall()
    conn.close()
    return registros

def sincronizar_ponto():
    conn = conectar_ponto()
    resultado = salvar_dados_ponto_no_arquivo(conn)  
    if resultado:
        commit_to_github(PONTO_DB_FILE, "Sincronização manual de ponto.db")
    conn.close()
    return resultado
