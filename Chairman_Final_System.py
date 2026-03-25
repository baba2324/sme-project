import os
import requests
import threading
import time
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'SME_MASTER_FINAL.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

TELEGRAM_TOKEN = "8697049954:AAEHNS-BqSTgdZ-yHEDtBa7Ic_Myntc6gH4"
CHAT_ID = "7013080778"

class BusinessLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    biz_name = db.Column(db.String(100))
    owner_name = db.Column(db.String(50))
    phone = db.Column(db.String(20), unique=True)
    workers = db.Column(db.String(20))
    sales = db.Column(db.String(50))
    goal = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def fishing_bot():
    while True:
        time.sleep(3600)

HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SME 통합지원센터</title>
<style>
body{background:#0f172a;color:white;font-family:sans-serif;padding:20px}
input,select{width:100%;padding:12px;margin:8px 0}
button{background:#fbbf24;padding:15px;width:100%;font-weight:bold}
</style>
</head>
<body>

<h2>SME 통합지원센터</h2>

<input id="biz" placeholder="회사명">
<input id="owner" placeholder="대표자">
<input id="phone" placeholder="전화번호">

<select id="goal">
<option value="고용지원금">고용지원금</option>
<option value="세금">세금</option>
</select>

<button onclick="send()">신청</button>

<script>
async function send(){
const data={
biz:biz.value,
owner:owner.value,
phone:phone.value,
goal:goal.value
}
await fetch('/api/v1/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
alert("완료")
}
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/v1/submit', methods=['POST'])
def submit():
    data = request.json
    new = BusinessLead(
        biz_name=data['biz'],
        owner_name=data['owner'],
        phone=data['phone'],
        goal=data['goal']
    )
    db.session.add(new)
    db.session.commit()

    msg = f"{data['biz']} / {data['phone']}"
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                  json={"chat_id": CHAT_ID, "text": msg})

    return jsonify({"ok": True})

if __name__ == '__main__':
    threading.Thread(target=fishing_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)