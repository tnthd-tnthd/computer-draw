
from flask import Flask, render_template, request, redirect, url_for, session
import random, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'

applicants = []
winners = []
ADMIN_PASSWORD = "secret1234"

@app.route("/")
def index():
    return render_template("index.html", applicants=applicants, winners=winners, is_admin=session.get("is_admin", False))

@app.route("/apply", methods=["POST"])
def apply():
    name = request.form.get("name")
    if name and name not in applicants:
        applicants.append(name)
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
    if len(applicants) <= 4:
        winners = applicants[:]
    else:
        winners = random.sample(applicants, 4)

    today = datetime.today().strftime('%Y-%m-%d')
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
