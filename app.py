from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import bd as bd
import csv
import json
from io import StringIO
from os import environ
import subprocess
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

with app.app_context():
    bd.criar_tabela_usuarios()
    bd.criar_tabela_ponto()
    print("Tabelas inicializadas com sucesso")

## download de tabelas
@app.route('/api/sincronizar', methods=['POST'])
def sincronizar():
    """Endpoint para sincronização manual"""
    try:
        success = bd.sincronizar_usuarios()
        if success:
            return jsonify({'status': 'success', 'message': 'Dados sincronizados com sucesso'})
        else:
            return jsonify({'status': 'error', 'message': 'Erro ao sincronizar dados'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Erro: {str(e)}'}), 500
@app.route('/api/estado', methods=['GET'])

def estado_db():
    """Endpoint para verificar estado do database"""
    try:
        conn = bd.conectar_usuarios()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM usuarios')
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'usuarios_count': count,
            'modo_memoria': bd.USE_MEMORY_DB
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def restaurar_bancos():
    """Clona repositório privado com os .db e copia para a pasta atual."""
    token = os.environ.get("GITHUB_TOKEN")
    repo_url = os.environ.get("DB_REPO_URL")
    if not token or not repo_url:
        print("⚠️ Variáveis de ambiente GITHUB_TOKEN ou DB_REPO_URL não configuradas.")
        return
    
    clone_dir = "/tmp/db_repo"
    if os.path.exists(clone_dir):
        subprocess.run(["rm", "-rf", clone_dir])

    auth_url = repo_url.replace("https://", f"https://{token}@")

    print("📥 Clonando repositório privado de bancos...")
    subprocess.run(["git", "clone", auth_url, clone_dir], check=True)

    # Copia todos os .db para o diretório atual
    for file in os.listdir(clone_dir):
        if file.endswith(".db"):
            subprocess.run(["cp", os.path.join(clone_dir, file), file])
            print(f"✅ Banco restaurado: {file}")


def enviar_backup():
    """Envia os .db atuais para o repositório privado no GitHub."""
    token = os.environ.get("GITHUB_TOKEN")
    repo_url = os.environ.get("DB_REPO_URL")
    if not token or not repo_url:
        print("⚠️ Variáveis de ambiente GITHUB_TOKEN ou DB_REPO_URL não configuradas.")
        return
    
    clone_dir = "/tmp/db_repo"
    if os.path.exists(clone_dir):
        subprocess.run(["rm", "-rf", clone_dir])

    auth_url = repo_url.replace("https://", f"https://{token}@")

    print("📤 Clonando repositório privado para backup...")
    subprocess.run(["git", "clone", auth_url, clone_dir], check=True)

    # Copia todos os .db para o repositório
    for file in os.listdir("."):
        if file.endswith(".db"):
            subprocess.run(["cp", file, os.path.join(clone_dir, file)])
            print(f"🔄 Banco atualizado para backup: {file}")

    # Commit e push
    subprocess.run(["git", "-C", clone_dir, "add", "."], check=True)
    subprocess.run(["git", "-C", clone_dir, "commit", "-m", "Backup automático"], check=False)
    subprocess.run(["git", "-C", clone_dir, "push"], check=True)
    print("✅ Backup enviado com sucesso para o GitHub.")


# Executa a restauração antes de inicializar os bancos
restaurar_bancos()

# garantir estruturas
bd.criar_tabela_usuarios()
bd.criar_tabela_ponto()
bd.criar_tabela_categorias()

## MANEJO DO USUÁRIO
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = bd.autenticar_usuario(data['username'], data['senha'])
    if user:
        return jsonify({'status': 'success', 'user': user[1]})
    return jsonify({'status': 'error', 'message': 'Usuário ou senha inválidos'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    token = data.get('secure_psw')
    if token != os.environ.get("ADMIN_TOKEN"):
        return jsonify({'status': 'error', 'message': 'Acesso negado'}), 403

    success = bd.cadastrar_usuario(data['username'], data['email'], data['senha'])
    enviar_backup()
    return jsonify({'status': 'success' if success else 'error'})


@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    if data['key_phrase'] != os.environ.get("ADMIN_TOKEN"):
        return jsonify({'status': 'error', 'message': 'Frase de segurança incorreta'}), 403
    bd.redefinir_senha(data['email'], data['nova_senha'], data['key_phrase'])
    enviar_backup()
    return jsonify({'status': 'success'})

# ----- LISTAR / CRIAR / DELETAR TABELAS -----
@app.route('/api/tabelas', methods=['GET'])
def listar_tabelas():
    return jsonify({'tabelas': bd.carregar_tabelas()})


@app.route('/api/tabelas', methods=['POST'])
def criar_tabela():
    data = request.json or {}
    nome = data.get('nome')
    tipo = data.get('tipo')

    if not nome or not tipo:
        return jsonify({'status': 'error', 'message': 'nome e tipo obrigatórios'}), 400

    existentes = bd.carregar_tabelas()
    if any(t['table_name'].lower() == nome.lower() for t in existentes):
        return jsonify({'status': 'error', 'message': 'Essa tabela já existe.'}), 400

    try:
        if tipo == 'anticorpo':
            bd.criar_tabelas_anticorpos(nome)
        else:
            bd.criar_tabelas_estoque(nome)
        bd.salvar_tabela(nome, tipo)
        return jsonify({'status': 'success'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/tabelas/<string:nome>', methods=['DELETE'])
def deletar_tabela(nome):
    try:
        bd.remover_categoria(nome)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ----- LISTAR / INSERIR / DELETAR ITENS -----
@app.route('/api/tabela', methods=['GET'])
def listar_itens_tabela():
    nome = request.args.get('nome')
    if not nome:
        return jsonify({'status': 'error', 'message': 'Nome obrigatório.'}), 400

    tabelas = bd.carregar_tabelas()
    entry = next((t for t in tabelas if t['table_name'] == nome), None)
    if not entry:
        return jsonify({'status': 'error', 'message': 'Tabela não encontrada.'}), 404

    tipo = entry['table_type']

    if tipo == 'anticorpo':
        rows = bd.listar_itens_anticorpo(nome)
        items = [{
            'id': r[0], 'codigo': r[1], 'nome': r[2], 'alvo': r[3],
            'host': r[4], 'conjugado': r[5], 'marca': r[6],
            'aliquotas': r[7], 'vials': r[8],
            'data_modificacao': r[9], 'nome_usuario': r[10]
        } for r in rows]
    else:
        rows = bd.listar_itens(nome)
        items = [{
            'id': r[0], 'item': r[1], 'infos': r[2],
            'quantidade': r[3], 'data_modificacao': r[4],
            'nome_usuario': r[5]
        } for r in rows]

    return jsonify({'table_type': tipo, 'items': items})


@app.route('/api/tabela', methods=['POST'])
def inserir_item_tabela():
    data = request.json or {}
    nome = data.get('nome')
    tipo = data.get('tipo')
    usuario = data.get('usuario') or 'unknown'

    if not nome or not tipo:
        return jsonify({'status': 'error', 'message': 'nome e tipo obrigatórios'}), 400

    try:
        if tipo == 'anticorpo':
            bd.inserir_item_anticorpo(
                nome,
                data.get('codigo', ''), data.get('nome', ''),
                data.get('alvo', ''), data.get('host', ''),
                data.get('conjugado', ''), data.get('marca', ''),
                float(data.get('aliquotas') or 0),
                float(data.get('vials') or 0),
                usuario
            )
        else:
            bd.inserir_item_estoque(
                nome,
                data.get('item', ''), data.get('infos', ''),
                float(data.get('quantidade') or 0),
                usuario
            )
        return jsonify({'status': 'success'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/tabela/item', methods=['DELETE'])
def deletar_item_tabela():
    data = request.json or {}
    nome = data.get('nome')
    item_id = data.get('item_id')
    tipo = data.get('tipo')

    if not nome or not item_id or not tipo:
        return jsonify({'status': 'error', 'message': 'nome, item_id e tipo são obrigatórios'}), 400

    try:
        bd.deletar_item(nome, item_id, tipo)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ----- EXPORTAR PARA CSV -----
@app.route('/api/tabela/export', methods=['GET'])
def export_tabela_csv():
    nome = request.args.get('nome')
    if not nome:
        return jsonify({'status': 'error', 'message': 'Nome obrigatório'}), 400

    tabelas = bd.carregar_tabelas()
    entry = next((t for t in tabelas if t['table_name'] == nome), None)
    if not entry:
        return jsonify({'status': 'error', 'message': 'Tabela não encontrada'}), 404

    tipo = entry['table_type']
    output = StringIO()
    writer = csv.writer(output)

    if tipo == 'anticorpo':
        writer.writerow(['id', 'codigo', 'nome', 'alvo', 'host', 'conjugado', 'marca', 'aliquotas', 'vials', 'data_modificacao', 'nome_usuario'])
        writer.writerows(bd.listar_itens_anticorpo(nome))
    else:
        writer.writerow(['id', 'item', 'infos', 'quantidade', 'data_modificacao', 'nome_usuario'])
        writer.writerows(bd.listar_itens(nome))

    output.seek(0)
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={nome}.csv'})

# ----- PONTO (mantido) -----
@app.route('/api/ponto', methods=['POST'])
def registrar_ponto():
    data = request.json
    bd.registrar_ponto(data.get('usuario'), data.get('data'), data.get('entrada'), data.get('saida'))
    return jsonify({'status': 'success'})


@app.route('/api/exportar_ponto', methods=['GET'])
def exportar_ponto():
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'status': 'error', 'message': 'Usuário não especificado'}), 400

    conn = bd.conectar_ponto()
    cursor = conn.cursor()
    cursor.execute('SELECT data, hora_entrada, hora_saida FROM ponto WHERE nome_usuario = ?', (usuario,))
    registros = cursor.fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Data', 'Hora de Entrada', 'Hora de Saída'])
    writer.writerows(registros)

    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=ponto_{usuario}.csv'}
    )

### BACKUP
@app.route('/api/backup', methods=['POST'])
def backup():
    key = request.args.get('key')
    if key != os.environ.get("ADMIN_TOKEN"):
        return jsonify({'status': 'error', 'message': 'Chave incorreta'}), 403
    enviar_backup()
    return jsonify({'status': 'success', 'message': 'Backup enviado com sucesso.'})


# ---- static single-page serving (opcional) ----
@app.route('/')
def index():
    return send_from_directory('frontend', 'home.html')  # ajuste conforme estrutura

if __name__ == '__main__':
    port = int(environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
