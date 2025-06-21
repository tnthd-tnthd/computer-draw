
from flask import Flask, render_template, request, redirect, url_for, session
import random, json
from datetime import datetime
import os

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
def draw():
    if not session.get("is_admin"):
        return "관리자만 사용할 수 있습니다.", 403

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

        # 기록 저장
        history = []
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                history = json.load(f)

        history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "winners": winners
        })

        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print("❌ 오류 발생:", e)

    return redirect(url_for("index"))

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
