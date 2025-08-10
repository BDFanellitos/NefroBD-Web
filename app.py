from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import bd as bd
import csv
import json
from io import StringIO
from os import environ

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

## garantir estruturas
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
    success = bd.cadastrar_usuario(data['username'], data['email'], data['senha'])
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Usuário ou email já cadastrados'}), 409
    
@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    if data['key_phrase'] != 'alohomora':
        return jsonify({'status': 'error', 'message': 'Frase de segurança incorreta'}), 403
    bd.redefinir_senha(data['email'], data['nova_senha'], data['key_phrase'])
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


# ---- static single-page serving----
@app.route('/')
def index():
    return send_from_directory('frontend', 'home.html')  

if __name__ == '__main__':
    port = int(environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
