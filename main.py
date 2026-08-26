import os, requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PUB = "pk_live_PlChNcPRqiFie0Mgh1bS9UI6RlTvO4tz"
SEC = "sk_live_3a004644009e504619bc9f85ae21f09cbc32ea554aa0a302d06613b1bd80f771"
HEADERS = {'X-API-Key': PUB, 'X-API-Secret': SEC, 'Content-Type': 'application/json'}
API = 'http://geniuspay.ci/api/v1/merchant/payments'
PACKS = {"hebdo": 1100, "mensuel": 3800}

premium_users = {}

@app.route('/init-payment', methods=['POST'])
def init_payment():
    data = request.json
    if not data:
        return jsonify({"error": "Donnees manquantes"}), 400
    p = data.get('pack')
    user_id = data.get('user_id', '')
    if p not in PACKS:
        return jsonify({"error": "Pack invalide"}), 400
    try:
        # 1. Lister les refs existantes AVANT
        r1 = requests.get(API, headers=HEADERS, timeout=10)
        old_refs = set()
        if r1.status_code == 200:
            d1 = r1.json()
            if isinstance(d1, dict) and isinstance(d1.get('data'), list):
                for item in d1['data']:
                    old_refs.add(item.get('reference', ''))

        # 2. Creer le nouveau paiement
        r2 = requests.post(API, headers=HEADERS,
            json={'amount': PACKS[p], 'description': 'Acces Winia AI - ' + p},
            timeout=15)

        # 3. Lister les refs APRES pour trouver la nouvelle
        r3 = requests.get(API, headers=HEADERS, timeout=10)
        new_ref = ''
        if r3.status_code == 200:
            d3 = r3.json()
            if isinstance(d3, dict) and isinstance(d3.get('data'), list):
                for item in d3['data']:
                    ref = item.get('reference', '')
                    if ref and ref not in old_refs:
                        new_ref = ref
                        break

        if new_ref:
            checkout = 'http://geniuspay.ci/checkout/' + new_ref
            return jsonify({
                "checkout_url": checkout,
                "payment_url": checkout,
                "reference": new_ref,
                "success": True
            })
        else:
            return jsonify({"error": "Impossible de trouver la nouvelle reference", "success": False}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook_genius():
    data = request.json
    if not data:
        return jsonify({"error": "Donnees invalides"}), 400
    event = data.get("event", "")
    transaction = data.get("data", {}).get("transaction", {})
    metadata = transaction.get("metadata", {})
    user_id = metadata.get("user_id", "")
    statut = transaction.get("status", "")
    if event == "payment.success" or statut == "completed":
        if user_id:
            premium_users[user_id] = True
        return jsonify({"success": True}), 200
    return jsonify({"success": False}), 200

@app.route('/api/statut-user/<user_id>', methods=['GET'])
def statut_user(user_id):
    is_premium = premium_users.get(user_id, False)
    return jsonify({"statut": "premium" if is_premium else "free"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
    
