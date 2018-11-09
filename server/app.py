import json
import jsonpickle

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import Namespace, SocketIO, emit, send

from server.translate import test
from server.speechtotext import *
from server.language import *
from server.stream import *
from server.punctuate import *

app = Flask(__name__)
CORS(app, resources={r"/subtitle": {"origins": "*"}, "/stream": {"origins": "*"}, "/stream-subtitle": {"origins": "*"}
, "/set-language": {"origins": "*"}, "/get-language": {"origins": "*"}})
socketio = SocketIO(app)
# streamer = None
# language = ""

# Main pipeline. Will return the JSON response with the translated text.
# def process(audio, sample_rate, lang, raw_pcm=False):
#     if lang == '':
#         lang = detect_language(audio)

#     transcript = get_text_from_pcm(audio, sample_rate, lang) if raw_pcm else \
#                  get_text(audio, sample_rate, lang)

#     translated = translate(transcript, 'en', lang.split('-')[0])
#     #punctuated = punctuate_subtitle(translated) if translated != "" else ""
#     return jsonify(subtitle=translated, lang=lang)

# def process_with_video(video, audio, sample_rate, lang):
#     no_punctuation = False
#     if lang == '':
#         #TODO: Move the split into the detect_language function
#         lang = detect_language(audio)
#         no_punctuation = True


#     transcript = get_text(audio, sample_rate, lang)
#     translated = translate(transcript, 'en', lang.split('-')[0])
#     if (no_punctuation):
#         return jsonify(video=jsonpickle.encode(video), subtitle=translated, lang=lang)
#     punctuated = punctuate_subtitle(translated) if translated != "" else ""

#     return jsonify(video=jsonpickle.encode(video), subtitle=punctuated, lang=lang)

# def _initialise_streamer(url):
#     global streamer

#     streamer = VideoStreamer(url)

#     try:
#         streamer.start()
#     except Exception:
#         return _error_response( "StreamlinkUnavailable ")

# def _error_response(error):
#     return jsonify(subtitle="", lang="", error=error)

# ################# REST ENDPOINTS #################

@app.route("/")
def hello():
    with open("playlist.m3u8", "a") as myfile:
        myfile.write("#EXT-X-DISCONTINUITY\n")
        myfile.write("#EXTINF:2.500,\n")
        myfile.write("temp2.ts\n")
        myfile.write("#EXT-X-DISCONTINUITY\n")
        myfile.write("#EXTINF:2.500,\n")
        myfile.write("temp2.ts\n")
        myfile.write("#EXT-X-DISCONTINUITY\n")
        myfile.write("#EXTINF:2.500,\n")
        myfile.write("temp2.ts\n")
    return "Polyglot - Live Subtitles - ICL"


# @app.route("/subtitle", methods=['POST'])
# def subtitle():
#     request_body = json.loads(request.data)

#     audio = request_body['audio']
#     sample_rate = request_body['sampleRate']
#     lang = request_body['lang']

#     return process(audio, sample_rate, lang, raw_pcm=True)

# @app.route("/set-language", methods=['POST'])
# def select_language():
#     global language
#     language = str(request.data).split('\'')[1]
#     return "Success"

# @app.route("/get-language", methods=['GET'])
# def get_language():
#     global language
#     return language

# @app.route("/stream", methods=['POST'])
# def stream():
#     global streamer

#     if streamer == None:
#         _initialise_streamer(json.loads(request.data)['url'])

#     lang = json.loads(request.data)['lang']
#     (video, audio) = streamer.get_data()
#     sample_rate    = streamer.get_sample_rate()

#     return process_with_video(video, audio, sample_rate, lang)

# @app.route("/translate-test")
# def dummyTranslate():
#     return test()

@app.route('/temp/<path:filename>')
def sendVideo(filename):
    return send_file(filename)

################# SOCKETS #################

class StreamingSocket(Namespace):

    streamer = None
    language = None

    def _initialise_streamer(self, url):
        self.streamer = VideoStreamer(url)

        try:
            self.streamer.start()
        except Exception:
            emit('stream-response', jsonify(video="", subtitle="", error="Streamlink Unavailable!"))

    def on_connect(self):
        print("Connected to client")

    def on_disconnect(self):
        self.streamer.stop()
        print("Disconnected from client")

    def on_stream(self, data):
        if self.streamer == None:
            self._initialise_streamer(data['url'])

        lang = data['lang']

        if lang == '':
            (video, audio) = self.streamer.get_data()
            lang = detect_language(audio)

        self.language = lang

        print("Successfully initialised streamer. Ready to stream!")

        emit('stream-response', json.dumps({'video':'', 'subtitles':''}))

    def on_ready(self):
        print("Ready to send data to client...")
        (video, audio) = self.streamer.get_data()
        sample_rate    = self.streamer.get_sample_rate()

        transcript = get_text(audio, sample_rate, self.language)
        translated = translate(transcript, 'en', self.language.split('-')[0])

        response = json.dumps({'video':jsonpickle.encode(video), 'subtitles':translated})

        print("Sending response: " + response)
        emit('stream-response', response)

socketio.on_namespace(StreamingSocket('/stream'))


# @socketio.on('connect')
# def test_connect():
#     print("Socket connected to client")

# @socketio.on('stream')
# def stream(payload):
#     print("Hit Stream Handler.")
#     print("URL: " + payload["url"])
#     print("Language: " + payload["lang"])
#     emit("stream-response", {"video": "BYTEARRAY", "subtitle": "hello this is text"})

# @socketio.on("audioprocess")
# def audioprocess(payload):
#     print(payload["sampleRate"])
#     print(type(payload["sampleRate"]))
#     print(payload["lang"])
#     print(type(payload["lang"]))
#     print(payload["audio"][0:5])
#     print(type(payload["audio"]))
#     subtitle = get_subtitle(payload['audio'], payload['sampleRate'], payload['lang'])
#     emit("subtitle", { "subtitle": subtitle })

if __name__ == '__main__':
    socketio.run(app)
