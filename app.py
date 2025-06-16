
from flask import Flask, render_template, request, redirect, url_for, session
import random, json
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key'

ADMIN_PASSWORD = "secret1234"

users = {}  # username: password
weights = {}  # username: weight
applicants = []
winners = []

@app.route("/")
def index():
    username = session.get("username")
    return render_template("index.html", applicants=applicants, winners=winners, is_admin=is_admin(), username=username)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users:
            return "이미 존재하는 사용자입니다."
        users[username] = password
        weights[username] = 1  # 기본 가중치
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            session["admin_ip"] = request.remote_addr
            return redirect(url_for("index"))
        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("index"))
        return "로그인 실패. <a href='/login'>다시 시도</a>"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/apply", methods=["POST"])
def apply():
    username = session.get("username")
    if not username:
        return "로그인 후 신청할 수 있습니다.", 403
    if username in applicants:
        return "이미 신청하셨습니다.", 403
    applicants.append(username)
    return redirect(url_for("index"))

@app.route("/clear", methods=["POST"])
def clear():
    global applicants, winners
    applicants = []
    winners = []
    return redirect(url_for("index"))

@app.route("/draw", methods=["POST"])
def draw():
    if not is_admin():
        return "관리자만 사용할 수 있습니다.", 403

    global winners
    if len(applicants) <= 4:
        winners = applicants[:]
    else:
        draw_pool = []
        for name in applicants:
            draw_pool.extend([name] * weights.get(name, 1))
        winners = random.sample(draw_pool, 4)
        winners = list(dict.fromkeys(winners))[:4]  # 중복 제거

    today = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d')
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
    except:
        history = {}

    history[today] = winners
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return redirect(url_for("index"))

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if not is_admin():
        return "관리자만 접근할 수 있습니다.", 403

    if request.method == "POST":
        for username in users:
            new_weight = request.form.get(username)
            if new_weight and new_weight.isdigit():
                weights[username] = int(new_weight)

    return render_template("admin.html", users=users, weights=weights)

@app.route("/history")
def history():
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
    except:
        history = {}
    return render_template("history.html", history=history)

def is_admin():
    return session.get("is_admin") and session.get("admin_ip") == request.remote_addr

def auto_clear_applicants():
    global applicants, winners
    while True:
        now = datetime.utcnow() + timedelta(hours=9)
        if now.hour == 0 and now.minute == 0:
            applicants = []
            winners = []
            time.sleep(60)
        time.sleep(30)

threading.Thread(target=auto_clear_applicants, daemon=True).start()
