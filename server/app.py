from flask import Flask
from flask_cors import CORS
from flask import request
from server.speechtotext import *
import json
from flask_socketio import SocketIO, emit
from server.translate import test
from server.stream import *

app = Flask(__name__)
CORS(app, resources={r"/subtitle": {"origins": "*"}, "/stream": {"origins": "*"}})
socketio = SocketIO(app)

@app.route("/")
def hello():
    return "Polyglot - Live Subtitles - ICL"

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
    print(payload["sampleRate"])
    print(type(payload["sampleRate"]))
    print(payload["lang"])
    print(type(payload["lang"]))
    print(payload["audio"][0:5])
    print(type(payload["audio"]))
    subtitle = get_subtitle(payload['audio'], payload['sampleRate'], payload['lang'])
    emit("subtitle", { "subtitle": subtitle })

@app.route("/stream", methods=['POST'])
def stream():
    url = json.loads(request.data)['url']
    lang = json.loads(request.data)['lang']
    print(url)
    print(lang)
    streamer = Streamer(url)
    response = streamer.start()
    if (response == None):
        return "{\"subtitle\": \"none\", \"lang\": \"\"}"
    else:
        audio = streamer.get_data(5)
        sample_rate = streamer.get_sample_rate()
        print(sample_rate)
        return get_subtitle_with_wav(audio, sample_rate, "fr-FR")

@app.route("/translate-test")
def dummyTranslate():
    return test()

if __name__ == '__main__':
    socketio.run(app)
