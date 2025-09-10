from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import bd as bd
import csv
from io import StringIO

app = Flask(__name__)
CORS(app)  

# Inicializar tabelas
with app.app_context():
    bd.criar_tabela_usuarios()
    bd.criar_tabela_ponto()
    print("Tabelas inicializadas com sucesso")

# ==============================
# USUÁRIOS
# ==============================
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
    result = bd.cadastrar_usuario(data['username'], data['email'], data['senha'])
    if result['success']:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': result['error']}), 409

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    if data['key_phrase'] != 'alohomora':
        return jsonify({'status': 'error', 'message': 'Frase de segurança incorreta'}), 403
    bd.redefinir_senha(data['email'], data['nova_senha'], data['key_phrase'])
    return jsonify({'status': 'success'})

@app.route('/api/estado', methods=['GET'])
def estado_db():
    try:
        conn = bd.conectar_usuarios()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM usuarios')
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({'status': 'success', 'usuarios_count': count, 'modo_memoria': bd.USE_MEMORY_DB})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==============================
# TABELAS
# ==============================
import json
def carregar_tabelas():
    try:
        with open("tabelas_criadas.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def salvar_tabelas(lista):
    with open("tabelas_criadas.json", "w") as f:
        json.dump(lista, f, indent=4)

@app.route('/api/criar_tabela', methods=['POST'])
def criar_tabela():
    data = request.json
    nome, tipo = data['nome'], data['tipo']
    tabelas = carregar_tabelas()

    if any(t['table_name'].lower() == nome.lower() for t in tabelas):
        return jsonify({'status': 'error', 'message': 'Essa tabela já existe.'}), 400

    if tipo == 'anticorpo':
        bd.criar_tabelas_anticorpos(nome)
    else:
        bd.criar_tabelas_estoque(nome)

    tabelas.append({"table_name": nome, "table_type": tipo})
    salvar_tabelas(tabelas)
    return jsonify({'status': 'success'})

@app.route('/api/categorias', methods=['GET'])
def listar_tabelas():
    return jsonify({'tabelas': carregar_tabelas()})

# ==============================
# PONTO
# ==============================
@app.route('/api/ponto', methods=['POST'])
def registrar_ponto():
    data = request.json
    bd.registrar_ponto(data['usuario'], data['data'], data['entrada'], data.get('saida'))
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

    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename=ponto_{usuario}.csv'})

# ==============================
# FRONTEND
# ==============================
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('frontend', path)

# ==============================
# MAIN
# ==============================
if __name__ == '__main__':
    from os import environ
    port = int(environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)