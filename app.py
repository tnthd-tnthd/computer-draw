from flask import Flask, render_template, request, redirect, url_for
import random

app = Flask(__name__)

applicants = []
winners = []

@app.route("/", methods=["GET", "POST"])
def index():
    global applicants
    if request.method == "POST":
        name = request.form.get("name")
        if name and name not in applicants:
            applicants.append(name)
    return render_template("index.html", applicants=applicants, winners=winners)

@app.route("/draw", methods=["POST"])
def draw():
    global winners
    if len(applicants) <= 4:
        winners = applicants[:]
    else:
        winners = random.sample(applicants, 4)
    return redirect(url_for("index"))

@app.route("/reset", methods=["POST"])
def reset():
    global applicants, winners
    applicants = []
    winners = []
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
