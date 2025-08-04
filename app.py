from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import bd as bd
import json
import csv
from io import StringIO
from os import environ

app = Flask(__name__)
CORS(app, origins=["https://bdfanellitos.github.io"])  # Libera só o seu GitHub Pages

# Criar tabelas se não existirem
bd.criar_tabela_usuarios()
bd.criar_tabela_ponto()

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
    success = bd.cadastrar_usuario(data['username'], data['email'], data['senha'])
    if success:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Usuário ou email já cadastrados'}), 409

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    if data['key_phrase'] != 'alohomora':
        return jsonify({'status': 'error', 'message': 'Frase de segurança incorreta'}), 403
    bd.redefinir_senha(data['email'], data['nova_senha'], data['key_phrase'])
    return jsonify({'status': 'success'})

## MANEJO DE TABELAS
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
    nome = data['nome']
    tipo = data['tipo']

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
    tabelas = carregar_tabelas()
    return jsonify({'tabelas': tabelas})

## PONTO
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
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=ponto_{usuario}.csv'}
    )

# Início do servidor (Render usa PORT)
if __name__ == '__main__':
    port = int(environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
