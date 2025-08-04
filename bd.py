import sqlite3
import random
import string
import hashlib
import datetime
import os

# Funções de conexão
def conectar_usuarios():
    return sqlite3.connect('usuarios.db')

def conectar_estoque(categoria):
    return sqlite3.connect(f'{categoria}_estoque.db')

def conectar_ponto():
    return sqlite3.connect('ponto.db')

# Funções de manipulação de tabelas
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

def criar_tabelas_estoque(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {categoria}_estoque (
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
    ''')
    conn.commit()
    conn.close()

def deletar_tabela(categoria):
    db_file = f'{categoria}_estoque.db'
    
    if os.path.exists(db_file):
        os.remove(db_file)
        return f"Banco de dados '{db_file}' excluído com sucesso."
    else:
        return f"Banco de dados '{db_file}' não encontrado."

def listar_categorias():
    db_files = [f.replace('_estoque.db', '') for f in os.listdir() if f.endswith('_estoque.db')]
    return db_files

# Funções de manipulação de dados
def gerar_id_unico():
    return ''.join(random.choices(string.digits, k=6))

# Funções para 'usuarios.db'
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
        return None  # Retorna None se algum campo estiver vazio

    conn = conectar_usuarios()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE username = ? AND senha = ?', (username, hash_senha(senha)))
    user = cursor.fetchone()
    conn.close()
    return user


def redefinir_senha(email, nova_senha, key_phrase):
    key_phrase = 'alohomora'
    conn = conectar_usuarios()
    cursor = conn.cursor()
    cursor.execute('UPDATE usuarios SET senha = ? WHERE email = ?', (hash_senha(nova_senha), email))
    conn.commit()
    conn.close()

# Funções para '**_estoque.db'
def inserir_item_estoque(categoria, item, infos, quantidade, username):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    data_modificacao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item_id = gerar_id_unico()
    cursor.execute(f'INSERT INTO {categoria}_estoque (id, item, infos, quantidade, data_modificacao, nome_usuario) VALUES (?, ?, ?, ?, ?, ?)', 
                (item_id, item, infos, quantidade, data_modificacao, username))
    conn.commit()
    conn.close()

def inserir_item_anticorpo(categoria, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, username):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()

    data_modificacao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item_id = gerar_id_unico()

    cursor.execute(f'''
        INSERT INTO {categoria}_anticorpo (id, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, data_modificacao, nome_usuario) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (item_id, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, data_modificacao, username))
    
    conn.commit()
    conn.close()

def deletar_item(categoria, item_id, tipo_tabela):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    
    if tipo_tabela == "estoque":
        cursor.execute(f'DELETE FROM {categoria}_estoque WHERE id = ?', (item_id,))
    elif tipo_tabela == "anticorpo":
        cursor.execute(f'DELETE FROM {categoria}_anticorpo WHERE id = ?', (item_id,))
    
    conn.commit()
    conn.close()

def atualizar_estoque(categoria, item_id, coluna, nova_info):
        con = conectar_estoque(categoria)
        cursor = con.cursor()

        query = f"UPDATE {categoria}_estoque SET {coluna} = ? WHERE id = ?"
        cursor.execute(query, (nova_info, item_id))

        con.commit()
        con.close()

def atualizar_anticorpo(categoria, item_id, coluna, nova_info):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {categoria}_anticorpo SET {coluna} = ? WHERE id = ?", (nova_info, item_id))
    conn.commit()
    conn.close()

def listar_itens(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    cursor.execute(f'SELECT id, item, infos, quantidade, data_modificacao, nome_usuario FROM {categoria}_estoque')
    itens = cursor.fetchall()
    conn.close()
    return itens

def listar_itens_anticorpo(categoria):
    conn = conectar_estoque(categoria)
    cursor = conn.cursor()
    
    # Usar nome dinâmico da tabela
    cursor.execute(f'''
        SELECT id, codigo, nome, alvo, host, conjugado, marca, aliquotas, vials, data_modificacao, nome_usuario 
        FROM {categoria}_anticorpo
    ''')
    
    itens = cursor.fetchall()
    conn.close()
    return itens


# Funções para 'ponto.db'
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
