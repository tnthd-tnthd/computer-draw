
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from flask import Flask, render_template, request, redirect, url_for, session
import random, json
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key'

applicants = []  # list of dicts: {"name": str, "subjects": list}
winners = {}  # key: subject, value: winner name
winners = []
ADMIN_PASSWORD = "secret1234"

@app.route("/")
def index():
    return render_template("index.html", applicants=applicants, winners=winners, is_admin=session.get("is_admin", False))

@app.route("/apply", methods=["POST"])
def apply():
    name = request.form.get("name")
    subjects = request.form.getlist("subjects")
    if name and subjects:
        # 중복 신청 방지
        exists = any(a["name"] == name for a in applicants)
        if not exists:
            applicants.append({"name": name, "subjects": subjects})
    return redirect(url_for("index"))

@app.route("/clear", methods=["POST"])
def clear():
    global applicants, winners
    applicants = []  # list of dicts: {"name": str, "subjects": list}
winners = {}  # key: subject, value: winner name
    winners = []
    return redirect(url_for("index"))

@app.route("/draw", methods=["POST"])
def draw():
    global winners
    import random
    selected = {}
    subjects = ["수-1", "수-2", "수-3", "수-4"]
    for subject in subjects:
        # 해당 과목 신청자 필터링
        candidates = [a["name"] for a in applicants if subject in a["subjects"]]
        if candidates:
            selected[subject] = random.choice(candidates)
        else:
            selected[subject] = "신청자 없음"
    winners = selected
    if not session.get("is_admin"):
        return "관리자만 사용할 수 있습니다.", 403

    global winners
    if len(applicants) <= 4:
        winners = applicants[:]
    else:
        winners = random.sample(applicants, 4)

    today = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d')
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {}

    history[today] = winners

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("index"))
        else:
            return "비밀번호가 틀렸습니다. <a href='/login'>다시 시도</a>"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))

@app.route("/history")
def history():
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {}
    return render_template("history.html", history=history)

# ✅ 자정 자동 초기화 (KST 기준)
def auto_clear_applicants():
    while True:
        now = datetime.utcnow() + timedelta(hours=9)  # KST
        if now.hour == 0 and now.minute == 0:
            print("[자동 초기화] 신청자 목록을 초기화합니다 (KST 자정).")
            global applicants, winners
            applicants = []  # list of dicts: {"name": str, "subjects": list}
winners = {}  # key: subject, value: winner name
            winners = []
            time.sleep(60)
        time.sleep(30)

threading.Thread(target=auto_clear_applicants, daemon=True).start()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    
scheduler = BackgroundScheduler(timezone=timezone("Asia/Seoul"))

@scheduler.scheduled_job(CronTrigger(hour=20, minute=50))
def auto_draw():
    global winners
    import random
    selected = {}
    subjects = ["수-1", "수-2", "수-3", "수-4"]
    for subject in subjects:
        candidates = [a["name"] for a in applicants if subject in a["subjects"]]
        if candidates:
            selected[subject] = random.choice(candidates)
        else:
            selected[subject] = "신청자 없음"
    winners = selected
    print("✅ 자동 추첨 완료")

@scheduler.scheduled_job(CronTrigger(hour=0, minute=0))
def clear_everything():
    global applicants, winners
    applicants.clear()
    winners.clear()
    print("🧹 신청자 및 당첨자 초기화 완료")

scheduler.start()

    app.run(host="0.0.0.0", port=port)
