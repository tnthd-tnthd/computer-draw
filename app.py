from flask import Flask, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
import random

app = Flask(__name__)

applicants = []
winners = {}

@app.route("/")
def index():
    return render_template("index.html", applicants=applicants, winners=winners)

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    selected_subjects = request.form.getlist("subjects")
    if name and selected_subjects:
        applicants.append({"name": name, "subjects": selected_subjects})
    return redirect(url_for("index"))
def submit():
    name = request.form.get("name")
    selected_subjects = request.form.getlist("subjects")
    if name and selected_subjects:
        applicants.append({"name": name, "subjects": selected_subjects})
    return redirect(url_for("index"))

@app.route("/draw", methods=["POST"])
def draw():
    global winners
    winners = {}
    subjects = ["수-1", "수-2", "수-3", "수-4"]
    for subject in subjects:
        filtered = [a["name"] for a in applicants if subject in a["subjects"]]
        if filtered:
            winners[subject] = random.choice(filtered)
    return redirect(url_for("index"))

def auto_draw():
    now = datetime.now(pytz.timezone("Asia/Seoul"))
    if now.hour == 20 and now.minute == 50:
        with app.app_context():
            draw()

def reset_applicants():
    now = datetime.now(pytz.timezone("Asia/Seoul"))
    if now.hour == 0 and now.minute == 0:
        global applicants, winners
        applicants = []
        winners = {}

scheduler = BackgroundScheduler()
scheduler.add_job(auto_draw, "cron", minute="*", second="5")
scheduler.add_job(reset_applicants, "cron", minute="*", second="10")
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)