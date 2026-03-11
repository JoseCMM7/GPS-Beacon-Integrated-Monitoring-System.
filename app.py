from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/beacon', methods=['POST'])
def recibir_beacon():
    datos = request.get_json()
    
    print(f"[*] Alerta de Beacon recibida: {datos}")
    
    # Pendiente: Integración con SQLAlchemy para PostgreSQL
    
    return jsonify({"estado": "exito", "mensaje": "Lectura de geocerca registrada"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)