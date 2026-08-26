import os, requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PUB = "pk_live_PlChNcPRqiFie0Mgh1bS9UI6RlTvO4tz"
SEC = "sk_live_3a004644009e504619bc9f85ae21f09cbc32ea554aa0a302d06613b1bd80f771"
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
        r = requests.post('http://geniuspay.ci/api/v1/merchant/payments',
            headers={
                'X-API-Key': PUB,
                'X-API-Secret': SEC,
                'Content-Type': 'application/json'
            },
            json={
                'amount': PACKS[p],
                'description': 'Acces Winia AI Football - ' + p
            },
            timeout=15
        )
        resp = r.json()
        ref = ''
        if isinstance(resp, dict):
            d = resp.get('data', [])
            if isinstance(d, list) and len(d) > 0:
                ref = d[0].get('reference', '')
            elif isinstance(d, dict):
                ref = d.get('reference', '')
        if not ref:
            ref = resp.get('reference', '')

        if ref:
            checkout = 'http://geniuspay.ci/checkout/' + ref
            if user_id:
                premium_users[user_id + '_ref'] = ref
            return jsonify({
                "checkout_url": checkout,
                "payment_url": checkout,
                "reference": ref,
                "success": True
            })
        else:
            return jsonify({"error": "Pas de reference", "success": False}), 500
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
    
