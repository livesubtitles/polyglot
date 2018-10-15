from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Polyglot - Live Subtitles"

@app.route("/pablo")
def pablo():
    return "GOROSTIAGAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

