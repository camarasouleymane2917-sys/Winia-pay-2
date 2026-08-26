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
        # Creer le paiement
        requests.post(API, headers=HEADERS,
            json={'amount': PACKS[p], 'description': 'Acces Winia AI - ' + p},
            timeout=15)

        # Recuperer le dernier paiement cree (le plus recent)
        r = requests.get(API + '?per_page=1', headers=HEADERS, timeout=10)
        resp = r.json()

        ref = ''
        if isinstance(resp, dict):
            d = resp.get('data', [])
            if isinstance(d, list) and len(d) > 0:
                ref = d[0].get('reference', '')
            elif isinstance(d, dict):
                ref = d.get('reference', '')

        # Si pas trouve avec per_page, chercher le dernier page
        if not ref:
            r2 = requests.get(API, headers=HEADERS, timeout=10)
            resp2 = r2.json()
            if isinstance(resp2, dict):
                meta = resp2.get('meta', {})
                last_page = meta.get('last_page', 1)
                if last_page > 1:
                    r3 = requests.get(API + '?page=' + str(last_page), headers=HEADERS, timeout=10)
                    resp3 = r3.json()
                    d3 = resp3.get('data', [])
                    if isinstance(d3, list) and len(d3) > 0:
                        ref = d3[-1].get('reference', '')
                else:
                    d2 = resp2.get('data', [])
                    if isinstance(d2, list) and len(d2) > 0:
                        highest = max(d2, key=lambda x: x.get('id', 0))
                        ref = highest.get('reference', '')

        if ref:
            checkout = 'http://geniuspay.ci/checkout/' + ref
            return jsonify({"checkout_url": checkout, "reference": ref, "success": True})
        else:
            return jsonify({"error": "Reference introuvable", "success": False}), 500
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
    
