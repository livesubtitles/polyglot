import json
import jsonpickle

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from server.translate import test
from server.speechtotext import *
from server.language import *
from server.stream import *
from server.punctuate import *

app = Flask(__name__)
CORS(app, resources={r"/subtitle": {"origins": "*"}, "/stream": {"origins": "*"}, "/stream-subtitle": {"origins": "*"}
, "/set-language": {"origins": "*"}, "/get-language": {"origins": "*"}, "/punctuate": {"origins": "*"}})
socketio = SocketIO(app)
streamer = None
language = ""
first_request = True

# Main pipeline. Will return the JSON response with the translated text.
def process(audio, sample_rate, lang, raw_pcm=False):
    if lang == '':
        lang = detect_language(audio)

    transcript = get_text_from_pcm(audio, sample_rate, lang) if raw_pcm else \
                 get_text(audio, sample_rate, lang)

    translated = translate(transcript, 'en', lang.split('-')[0])
    #punctuated = punctuate_subtitle(translated) if translated != "" else ""
    return jsonify(subtitle=translated, lang=lang)

def process_with_video(video, audio, sample_rate, lang):
    if lang == '':
        #TODO: Move the split into the detect_language function
        lang = detect_language(audio)


    transcript = get_text(audio, sample_rate, lang)
    translated = translate(transcript, 'en', lang.split('-')[0])

    return jsonify(video=jsonpickle.encode(video), subtitle=translated, lang=lang)

def _initialise_streamer(url):
    global streamer

    streamer = VideoStreamer(url)

    try:
        streamer.start()
    except Exception:
        return _error_response( "StreamlinkUnavailable ")

def _error_response(error):
    return jsonify(subtitle="", lang="", error=error)

def prepare_model_file():
    f1 = open("./punctuator2/model1.pcl", "rb")
    final_file = open("./punctuator2/final-model.pcl", "wb")
    for line in f1:
        final_file.write(line)
    f1.close()
    print("Writing first file completed")
    f2 = open("./punctuator2/model2.pcl", "rb")
    for line in f2:
        final_file.write(line)
    f2.close()
    print("Writing second file completed")
    final_file.close()

################# REST ENDPOINTS #################

@app.route("/")
def hello():
    return "Polyglot - Live Subtitles - ICL"

@app.route("/subtitle", methods=['POST'])
def subtitle():
    request_body = json.loads(request.data)

    audio = request_body['audio']
    sample_rate = request_body['sampleRate']
    lang = request_body['lang']

    return process(audio, sample_rate, lang, raw_pcm=True)

@app.route("/set-language", methods=['POST'])
def select_language():
    global language
    language = str(request.data).split('\'')[1]
    return "Success"

@app.route("/get-language", methods=['GET'])
def get_language():
    global language
    return language

@app.route("/stream", methods=['POST'])
def stream():
    global streamer

    if streamer == None:
        _initialise_streamer(json.loads(request.data)['url'])

    lang = json.loads(request.data)['lang']
    (video, audio) = streamer.get_data()
    sample_rate    = streamer.get_sample_rate()

    return process_with_video(video, audio, sample_rate, lang)

@app.route("/translate-test")
def dummyTranslate():
    return test()

@app.route("/punctuate", methods=['POST'])
def punctuate():
    global first_request
    if (first_request):
        if (not os.path.isfile("./punctuator2/final-model.pcl")):
            prepare_model_file()
        model_path = "./punctuator2/final-model.pcl"
        init_punctuator(model_path)
        first_request = False
    request_body = json.loads(request.data)
    subtitle = request_body['subtitle']
    return jsonify(subtitle=punctuate_subtitle(subtitle))

################# SOCKETS #################

@socketio.on('connect')
def test_connect():
    print("Connected.")

@socketio.on('testevent')
def testevent(payload):
    print("Hello")

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


if __name__ == '__main__':
    socketio.run(app)
