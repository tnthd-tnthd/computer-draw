
from flask import Flask, render_template, request, redirect, url_for, session
import random, json
from datetime import datetime
import os
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

app = Flask(__name__)
app.secret_key = 'your-secret-key'

applicants = []
winners = []
ADMIN_PASSWORD = "secret1234"

@app.route("/")
def index():
    return render_template("index.html", 
                           applicants=[a['name'] for a in applicants], 
                           winners=[f"{w['name']} - {w['result']}" for w in winners], 
                           is_admin=session.get("is_admin", False))

@app.route("/apply", methods=["POST"])
def apply():
    name = request.form.get("name")
    choices = request.form.getlist("choices")
    if name and choices and not any(a['name'] == name for a in applicants):
        applicants.append({'name': name, 'choices': choices})
    return redirect(url_for("index"))

@app.route("/clear", methods=["POST"])
def clear():
    global applicants, winners
    applicants = []
    winners = []
    return redirect(url_for("index"))

@app.route("/draw", methods=["POST"])
def draw_manual():
    if not session.get("is_admin"):
        return "관리자만 사용할 수 있습니다.", 403
    perform_draw()
    return redirect(url_for("index"))

def perform_draw():
    global winners
    winners = []
    already_won = set()
    categories = ["수-1", "수-2", "수-3", "수-4"]

    try:
        for category in categories:
            eligible = [a for a in applicants if category in a['choices'] and a['name'] not in already_won]
            if eligible:
                selected = random.choice(eligible)
                winners.append({'name': selected['name'], 'result': category})
                already_won.add(selected['name'])

        history = []
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                history = json.load(f)

        history.append({
            "timestamp": datetime.now(timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S"),
            "winners": winners
        })

        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        print("✅ 자동 추첨 완료")

    except Exception as e:
        print("❌ 오류 발생:", e)

def clear_applicants():
    global applicants, winners
    applicants = []
    winners = []
    print("🧹 신청자 및 당첨자 초기화 완료")

# 스케줄러 설정
scheduler = BackgroundScheduler(timezone="Asia/Seoul")
scheduler.add_job(perform_draw, 'cron', hour=20, minute=50)
scheduler.add_job(clear_applicants, 'cron', hour=0, minute=0)
scheduler.start()

@app.route("/history")
def show_history():
    if not os.path.exists("history.json"):
        return render_template("history.html", history=[])
    with open("history.json", "r", encoding="utf-8") as f:
        history = json.load(f)
    return render_template("history.html", history=history)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))
