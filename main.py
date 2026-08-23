import os,requests
from flask import Flask,request,jsonify
app=Flask(__name__)
PUB=os.getenv("GENIUS_PUB","pk_sandbox_xxx")
SEC=os.getenv("GENIUS_SEC","sk_sandbox_xxx")
PACKS={"hebdo":1100,"mensuel":4000,"trimestriel":9400}
@app.route('/init-payment',methods=['POST'])
def init_payment():
 p=request.json.get('pack')
 if p not in PACKS: return jsonify({"error":"Pack invalide"}),400
 r=requests.post('http://geniuspay.ci/api/v1/merchant/payments',
 headers={'X-API-Key':PUB,'X-API-Secret':SEC,'Content-Type':'application/json'},
 json={'amount':PACKS[p],'description':f"Acces Winia AI Football - {p}"})
 return jsonify(r.json())
if __name__=='__main__':
 app.run(host='0.0.0.0',port=int(os.getenv("PORT",5000)))
  
