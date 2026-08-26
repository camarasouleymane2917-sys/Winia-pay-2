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
        payload = {
            'amount': PACKS[p],
            'description': 'Acces Winia AI Football - ' + p
        }
        r = requests.post('http://geniuspay.ci/api/v1/merchant/payments',
            headers={
                'X-API-Key': PUB,
                'X-API-Secret': SEC,
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=15
        )
        raw = r.json()

        checkout = ''
        reference = ''

        if isinstance(raw, dict):
            d = raw.get('data', {})
            if isinstance(d, dict):
                checkout = d.get('checkout_url', '') or d.get('payment_url', '')
                reference = d.get('reference', '')
            elif isinstance(d, list) and len(d) > 0:
                last = d[-1]
                if isinstance(last, dict):
                    checkout = last.get('checkout_url', '') or last.get('payment_url', '')
                    reference = last.get('reference', '')
            if not checkout:
                checkout = raw.get('checkout_url', '') or raw.get('payment_url', '')
                reference = raw.get('reference', '') or reference

        return jsonify({
            "checkout_url": checkout,
            "payment_url": checkout,
            "reference": reference,
            "success": bool(checkout)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug-geniuspay', methods=['POST'])
def debug_geniuspay():
    data = request.json or {}
    p = data.get('pack', 'mensuel')
    amount = PACKS.get(p, 3800)
    try:
        r = requests.post('http://geniuspay.ci/api/v1/merchant/payments',
            headers={
                'X-API-Key': PUB,
                'X-API-Secret': SEC,
                'Content-Type': 'application/json'
            },
            json={'amount': amount, 'description': 'Test Winia AI'},
            timeout=15
        )
        return jsonify({"status_code": r.status_code, "raw": r.json()})
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
    
