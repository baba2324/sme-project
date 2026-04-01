import os
import requests
import threading
import time
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# Render 환경에서는 절대 경로 설정을 더 확실히 해야 DB 유실이 없습니다.
basedir = os.path.abspath(os.path.dirname(__file__))

# DB 설정 (파일 이름을 조금 더 직관적으로 변경)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'sme_leads_v1.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Telegram 설정 (준용아, 이 부분은 나중에 환경변수로 빼는 게 보안상 좋다!)
TELEGRAM_TOKEN = "8697049954:AAEHNS-BqSTgdZ-yHEDtBa7Ic_Myntc6gH4"
CHAT_ID = "7013080778"

# DB 모델
class BusinessLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    biz_name = db.Column(db.String(100))
    owner_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    revenue = db.Column(db.String(20))
    employees = db.Column(db.String(20))
    support_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# 메인 페이지 HTML (디자인 보강 및 팝업 속도 조절)
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="7wYB7t4zjKLuG9iF6CBmUB__l6Hor19ddgDPHk0UeAY" />
    <title>SME 통합지원센터 | 2026 정부지원금 실시간 조회</title>
    <style>
        body{background:#0f172a;color:white;font-family:'Pretendard',sans-serif;margin:0;padding:0;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh}
        .main-content{text-align:center;padding:20px}
        h1{color:#fbbf24;font-size:28px;margin-bottom:10px}
        p{color:#94a3b8;margin-bottom:30px}
        .check-btn{background:#fbbf24;color:#0f172a;padding:18px 40px;font-weight:bold;border:none;border-radius:50px;font-size:18px;cursor:pointer;box-shadow:0 10px 15px -3px rgba(251,191,36,0.3)}
        
        /* 팝업 스타일 개선 */
        #popup{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:9999}
        .card{background:#1e293b;padding:30px;border-radius:24px;width:90%;max-width:400px;margin:50px auto;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5)}
        h3{margin-top:0;color:#fbbf24;text-align:center}
        input, select{width:100%;padding:14px;margin:10px 0;background:#0f172a;border:1px solid #334155;color:white;border-radius:12px;box-sizing:border-box;font-size:15px}
        .submit-btn{background:#fbbf24;padding:16px;width:100%;font-weight:bold;border:none;border-radius:12px;font-size:17px;cursor:pointer;margin-top:15px}
        .close-btn{background:transparent;color:#94a3b8;width:100%;padding:10px;border:none;cursor:pointer;margin-top:10px;text-decoration:underline}
    </style>
</head>
<body>

<div class="main-content">
    <h1>🔥 2026년 기업지원금 분석기</h1>
    <p>우리 회사 숨은 환급금, 1분 만에 확인하세요.</p>
    <button class="check-btn" onclick="openPopup()">지금 바로 조회하기</button>
</div>

<div id="popup">
    <div class="card">
        <h3>SME 데이터 분석 신청</h3>
        <input id="biz" placeholder="기업명 (법인/개인)">
        <input id="owner" placeholder="대표자 성함">
        <input id="phone" placeholder="연락처 (숫자만)">
        <input id="revenue" placeholder="매출액 (예: 10억)">
        <select id="employees">
            <option value="">직원 수 선택</option>
            <option value="5인미만">5인 미만</option>
            <option value="30인미만">30인 미만</option>
            <option value="30인이상">30인 이상</option>
        </select>
        <select id="support_type">
            <option value="">관심분야 선택</option>
            <option value="청년지원금">청년창업 지원금</option>
            <option value="정부정책자금">정부 정책자금</option>
            <option value="기업보험/절세">기업보험 및 절세</option>
        </select>
        <button class="submit-btn" id="subBtn" onclick="submitLead()">분석 결과 받기</button>
        <button class="close-btn" onclick="closePopup()">닫기</button>
    </div>
</div>

<script>
    // 0.5초 후 자동 팝업
    window.onload=function(){setTimeout(()=>openPopup(),500)}
    function openPopup(){document.getElementById('popup').style.display='block'}
    function closePopup(){document.getElementById('popup').style.display='none'}

    async function submitLead(){
        const btn = document.getElementById('subBtn');
        btn.innerText = "전송 중...";
        btn.disabled = true;

        const data={
            biz: document.getElementById('biz').value,
            owner: document.getElementById('owner').value,
            phone: document.getElementById('phone').value,
            revenue: document.getElementById('revenue').value,
            employees: document.getElementById('employees').value,
            support_type: document.getElementById('support_type').value
        }
        
        try {
            const res = await fetch('/api/v1/submit',{
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify(data)
            })
            if(res.ok){
                alert("성공적으로 접수되었습니다! 담당자가 곧 연락드립니다.");
                closePopup();
            }
        } catch(e) {
            alert("오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
        } finally {
            btn.innerText = "분석 결과 받기";
            btn.disabled = false;
        }
    }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

# 사이트맵 (구글 검색 노출용)
@app.route('/sitemap.xml')
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://sme-project.onrender.com/</loc>
            <lastmod>2026-04-01</lastmod>
            <priority>1.0</priority>
        </url>
    </urlset>"""
    return xml, 200, {'Content-Type': 'application/xml'}

@app.route('/api/v1/submit', methods=['POST'])
def submit():
    data = request.json
    new = BusinessLead(
        biz_name=data.get('biz'),
        owner_name=data.get('owner'),
        phone=data.get('phone'),
        revenue=data.get('revenue'),
        employees=data.get('employees'),
        support_type=data.get('support_type')
    )
    db.session.add(new)
    db.session.commit()

    # 텔레그램 알림 (가독성 좋게 수정)
    if TELEGRAM_TOKEN and CHAT_ID:
        msg = (f"🚨 [신규 지원금 상담 신청]\n"
               f"━━━━━━━━━━━━━━\n"
               f"🏢 기업명: {data.get('biz')}\n"
               f"👤 대표자: {data.get('owner')}\n"
               f"📞 연락처: {data.get('phone')}\n"
               f"💰 매출액: {data.get('revenue')}\n"
               f"👥 직원수: {data.get('employees')}\n"
               f"📝 유형: {data.get('support_type')}\n"
               f"━━━━━━━━━━━━━━")
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": msg})

    return jsonify({"ok": True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
