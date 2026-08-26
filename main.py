import os, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

PUB = os.getenv("GENIUS_PUB", "pk_sandbox_xxx")
SEC = os.getenv("GENIUS_SEC", "sk_sandbox_xxx")
PACKS = {"hebdo": 1100, "mensuel": 3800}

@app.route('/init-payment', methods=['POST'])
def init_payment():
    p = request.json.get('pack')
    if p not in PACKS: return jsonify({"error": "Pack invalide"}), 400
    r = requests.post('https://geniuspay.ci/api/v1/merchant/payments',
        headers={'X-API-Key': PUB, 'X-API-Secret': SEC, 'Content-Type': 'application/json'},
        json={'amount': PACKS[p], 'description': f"Acces Winia AI Football - {p}"})
    return jsonify(r.json())

@app.route('/webhook', methods=['POST'])
def webhook_genius():
    data = request.json
    if not data: return jsonify({"error": "Données invalides"}), 400
    statut = data.get("status")
    reference = data.get("reference") or data.get("data", {}).get("reference")
    if statut in ["success", "completed"]:
        # TODO: Mettre à jour ta base Turso ici pour activer l'accès de l'utilisateur
        return jsonify({"success": True, "message": "Paiement validé et accès accordé"}), 200
    return jsonify({"success": False, "message": "Statut ignoré"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
    
