import os
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# En production, il est préférable que l'application plante au démarrage 
# si les clés ne sont pas définies, plutôt que d'utiliser des clés sandbox par erreur.
PUB = os.getenv("GENIUS_PUB")
SEC = os.getenv("GENIUS_SEC")
PACKS = {"hebdo": 1100, "mensuel": 4000, "trimestriel": 9400}

@app.route('/init-payment', methods=['POST'])
def init_payment():
    p = request.json.get('pack') if request.is_json else None
    
    if not p or p not in PACKS: 
        return jsonify({"error": "Pack invalide"}), 400
        
    try:
        r = requests.post(
            'https://geniuspay.ci/api/v1/merchant/payments',
            headers={
                'X-API-Key': PUB, 
                'X-API-Secret': SEC, 
                'Content-Type': 'application/json'
            },
            json={
                'amount': PACKS[p], 
                'description': f"Acces Winia AI Football - {p}"
            },
            timeout=10 # Empêche ton serveur de bloquer si l'API est lente
        )
        
        # Vérifie si le code de statut HTTP est une erreur (ex: 400, 500)
        r.raise_for_status() 
        return jsonify(r.json()), 200
        
    except requests.exceptions.RequestException as e:
        # Enregistre l'erreur côté serveur, mais renvoie un message propre au client
        print(f"Erreur API de paiement : {e}")
        return jsonify({"error": "Erreur lors de l'initialisation du paiement"}), 502

@app.route('/webhook', methods=['POST'])
def webhook_genius():
    data = request.json
    if not data: 
        return jsonify({"error": "Données invalides"}), 400
        
    # --- SÉCURITÉ DU WEBHOOK ---
    # Remarque : Vérifie le nom exact du header dans la doc de GeniusPay
    signature = request.headers.get('X-Genius-Signature')
    if not signature:
        return jsonify({"error": "Signature manquante"}), 401
        
    # Recréer la signature pour vérifier l'authenticité
    payload = request.get_data()
    expected_sig = hmac.new(SEC.encode(), payload, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(signature, expected_sig):
        return jsonify({"error": "Signature invalide"}), 401
    # ---------------------------

    statut = data.get("status")
    reference = data.get("reference") or data.get("data", {}).get("reference")
    
    if statut in ["success", "completed"]:
        # TODO: Mettre à jour ta base Turso ici avec la 'reference'
        return jsonify({"success": True, "message": "Paiement validé"}), 200
        
    return jsonify({"success": False, "message": "Statut ignoré"}), 200

if __name__ == '__main__':
    if not PUB or not SEC:
        print("ATTENTION : Les variables d'environnement GENIUS_PUB ou GENIUS_SEC sont manquantes !")
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
    
