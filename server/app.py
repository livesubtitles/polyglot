from flask import Flask
from flask_cors import CORS
from flask import request
from server.speechtotext import *
import json
from flask_socketio import SocketIO, emit
from server.translate import test
from server.stream import *

app = Flask(__name__)
CORS(app, resources={r"/subtitle": {"origins": "*"}, "/stream": {"origins": "*"}, "/stream-subtitle": {"origins": "*"}
, "/set-language": {"origins": "*"}, "/get-language": {"origins": "*"}})
socketio = SocketIO(app)
streamer = None
language = ""

@app.route("/")
def hello():
    return "Polyglot - Live Subtitles - ICL"

@app.route("/subtitle", methods=['POST'])
def subtitle():
    request_body = json.loads(request.data)
    print(request_body['lang'])
    return get_subtitle(request_body['audio'], request_body['sampleRate'], request_body['lang'])

@app.route("/set-language", methods=['POST'])
def select_language():
    global language
    language = str(request.data).split('\'')[1]
    print(language)
    return "Success"

@app.route("/get-language", methods=['GET'])
def get_language():
    global language
    print ("Returning " + language)
    return language


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
    global streamer
    url = json.loads(request.data)['url']
    lang = json.loads(request.data)['lang']
    print(url)
    print(lang)
    streamer = Streamer(url)
    try:
        streamer.start()
        audio = streamer.get_data(5)
    except Exception:
        return "{\"subtitle\": \"none\", \"lang\": \"\"}"
    sample_rate = streamer.get_sample_rate()
    print(sample_rate)
    return get_subtitle_with_wav(audio, sample_rate, lang)

@app.route("/stream-subtitle", methods=['POST'])
def stream_subtitle():
    global streamer
    lang = json.loads(request.data)['lang']
    print(lang)
    audio = streamer.get_data(5)
    sample_rate = streamer.get_sample_rate()
    print(sample_rate)
    return get_subtitle_with_wav(audio, sample_rate, lang)

@app.route("/translate-test")
def dummyTranslate():
    return test()

if __name__ == '__main__':
    socketio.run(app)
