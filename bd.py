import sqlite3
import random
import string
import hashlib
import datetime
import os

BASE_DIR = os.path.dirname(__file__)

# DB paths
CATEGORIAS_DB = os.path.join(BASE_DIR, "categorias.db")
USUARIOS_DB = os.path.join(BASE_DIR, "usuarios.db")
PONTO_DB = os.path.join(BASE_DIR, "ponto.db")

# Funções de conexão
def conectar_usuarios():
    return sqlite3.connect(USUARIOS_DB)

def conectar_estoque(categoria):
    # cria db por categoria no mesmo diretório
    return sqlite3.connect(os.path.join(BASE_DIR, f'{categoria}_estoque.db'))

def conectar_ponto():
    return sqlite3.connect(PONTO_DB)

def conectar_categorias():
    return sqlite3.connect(CATEGORIAS_DB)


# --- CATEGORIAS (persistência das tabelas criadas) ---
def criar_tabela_categorias():
    conn = conectar_categorias()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT UNIQUE NOT NULL,
            table_type TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def carregar_tabelas():
    conn = conectar_categorias()
    cur = conn.cursor()
    cur.execute("SELECT table_name, table_type FROM categorias ORDER BY table_name")
    tabelas = [{"table_name": row[0], "table_type": row[1]} for row in cur.fetchall()]
    conn.close()
    return tabelas

def salvar_tabela(nome, tipo):
    conn = conectar_categorias()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO categorias (table_name, table_type) VALUES (?, ?)", (nome, tipo))
    conn.commit()
    conn.close()

def remover_categoria(nome):
    # remove entrada em categorias e o arquivo de DB da categoria se existir
    conn = conectar_categorias()
    cur = conn.cursor()
    cur.execute("DELETE FROM categorias WHERE table_name = ?", (nome,))
    conn.commit()
    conn.close()

    db_file = os.path.join(BASE_DIR, f'{nome}_estoque.db')
    if os.path.exists(db_file):
        os.remove(db_file)
        return True
    # também pode existir arquivo de anticorpo (mesmo sufixo em bd atual)
    return True


# --- USUÁRIOS ---
def criar_tabela_usuarios():
    conn = conectar_usuarios()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def gerar_id_unico():
    return ''.join(random.choices(string.digits, k=6))

def cadastrar_usuario(username, email, senha):
    conn = conectar_usuarios()
    cursor = conn.cursor()
    user_id = gerar_id_unico()
    try:
        cursor.execute('INSERT INTO usuarios (id, username, email, senha) VALUES (?, ?, ?, ?)', (user_id, username, email, hash_senha(senha)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def autenticar_usuario(username, senha):
    if not username or not senha:
        return None
    conn = conectar_usuarios()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE username = ? AND senha = ?', (username, hash_senha(senha)))
    user = cursor.fetchone()
    conn.close()
    return user

def redefinir_senha(email, nova_senha, key_phrase):
    conn = conectar_usuarios()
    cursor = conn.cursor()
    cursor.execute('UPDATE usuarios SET senha = ? WHERE email = ?', (hash_senha(nova_senha), email))
    conn.commit()
    conn.close()


# --- TABELAS DE CADA CATEGORIA ---
def criar_tabelas_estoque(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    # tabela com nome <categoria>_estoque
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS "{categoria}_estoque" (
        id TEXT PRIMARY KEY,
        item TEXT NOT NULL,
        infos TEXT,
        quantidade REAL NOT NULL,
        data_modificacao TEXT NOT NULL,
        nome_usuario TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def criar_tabelas_anticorpos(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{categoria}_anticorpo" (
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
    ''')
    conn.commit()
    conn.close()

def deletar_tabela(categoria):
    db_file = os.path.join(BASE_DIR, f'{categoria}_estoque.db')
    if os.path.exists(db_file):
        os.remove(db_file)
        return True
    return False

def listar_categorias_filesystem():
    # útil apenas se quiser varredura do fs
    db_files = [f.replace('_estoque.db', '') for f in os.listdir(BASE_DIR) if f.endswith('_estoque.db')]
    return db_files


# --- ITENS ---
def inserir_item_estoque(categoria, item, infos, quantidade, username):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    data_modificacao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item_id = gerar_id_unico()
    cursor.execute(f'INSERT INTO "{categoria}_estoque" (id, item, infos, quantidade, data_modificacao, nome_usuario) VALUES (?, ?, ?, ?, ?, ?)', 
                (item_id, item, infos, quantidade, data_modificacao, username))
    conn.commit()
    conn.close()
    return item_id

def inserir_item_anticorpo(categoria, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, username):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    data_modificacao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f'''
        INSERT INTO "{categoria}_anticorpo" (codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, data_modificacao, nome_usuario) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, data_modificacao, username))
    conn.commit()
    conn.close()

def deletar_item(categoria, item_id, tipo_tabela):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    if tipo_tabela == "estoque":
        cursor.execute(f'DELETE FROM "{categoria}_estoque" WHERE id = ?', (item_id,))
    elif tipo_tabela == "anticorpo":
        cursor.execute(f'DELETE FROM "{categoria}_anticorpo" WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

def atualizar_estoque(categoria, item_id, coluna, nova_info):
    con = conectar_estoque(categoria)
    cursor = con.cursor()
    query = f'UPDATE "{categoria}_estoque" SET {coluna} = ? WHERE id = ?'
    cursor.execute(query, (nova_info, item_id))
    con.commit()
    con.close()

def atualizar_anticorpo(categoria, item_id, coluna, nova_info):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f'UPDATE "{categoria}_anticorpo" SET {coluna} = ? WHERE id = ?', (nova_info, item_id))
    conn.commit()
    conn.close()

def listar_itens(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f'SELECT id, item, infos, quantidade, data_modificacao, nome_usuario FROM "{categoria}_estoque"')
    itens = cursor.fetchall()
    conn.close()
    return itens

def listar_itens_anticorpo(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT id, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, data_modificacao, nome_usuario 
        FROM "{categoria}_anticorpo"
    ''')
    itens = cursor.fetchall()
    conn.close()
    return itens


# --- PONTO ---
def criar_tabela_ponto():
    conn = conectar_ponto()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ponto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_usuario TEXT NOT NULL,
        data TEXT NOT NULL,
        hora_entrada TEXT NOT NULL,
        hora_saida TEXT
    )
    ''')
    conn.commit()
    conn.close()

def registrar_ponto(nome_usuario, data, hora_entrada, hora_saida=None):
    conn = conectar_ponto()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO ponto (nome_usuario, data, hora_entrada, hora_saida) VALUES (?, ?, ?, ?)', (nome_usuario, data, hora_entrada, hora_saida))
    conn.commit()
    conn.close()

def obter_pontos_usuario(nome_usuario):
    conn = conectar_ponto() 
    cursor = conn.cursor()
    cursor.execute('SELECT nome_usuario, data, hora_entrada, hora_saida FROM ponto WHERE nome_usuario = ?', (nome_usuario,))
    registros = cursor.fetchall()
    cursor.close()
    conn.close()
    return registros
