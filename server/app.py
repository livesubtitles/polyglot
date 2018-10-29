from flask import Flask
from flask_cors import CORS
from flask import request
from speechtotext import *
import json
from flask_socketio import SocketIO, emit
from translate import test

app = Flask(__name__)
CORS(app, resources={r"/subtitle": {"origins": "*"}})
socketio = SocketIO(app)

@app.route("/")
def hello():
    return "Polyglot - Live Subtitles - ICL"

@app.route("/pablo")
def pablo():
    return "GOROSTIAGAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

@app.route("/subtitle", methods=['POST'])
def subtitle():
    request_body = json.loads(request.data)
    print(request_body['lang'])
    return get_subtitle(request_body['audio'], request_body['sampleRate'], request_body['lang'])

@socketio.on('connect')
def test_connect():
    print("Connected.")
    emit('connection', {'data': 'Connected'})

@socketio.on("audioprocess")
def audioprocess(payload):
    print("Python payload " + str( payload ))

@app.route("/translate-test")
def dummyTranslate():
    return test()

if __name__ == '__main__':
    socketio.run(app)
