import json
import jsonpickle
import string
import random
import os
import shutil


from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, Namespace

from server.translate import test
from server.speechtotext import *
from server.language import *
from server.stream import *

app = Flask(__name__)
CORS(app, resources={r"/subtitle": {"origins": "*"}, "/stream": {"origins": "*"}, "/stream-subtitle": {"origins": "*"}
	, "/set-language": {"origins": "*"}, "/get-language": {"origins": "*"}, "/punctuate": {"origins": "*"},
	"/streams": {"origins": "*"}})
socketio = SocketIO(app)
streamer = None
language = ""

LOCAL_URL  = 'http://localhost:8000/'
SERVER_URL = 'https://ployglot-livesubtitles.herokuapp.com/'

# Main pipeline. Will return the JSON response with the translated text.
def process(audio, sample_rate, lang, raw_pcm=False):
	if lang == '':
		lang = detect_language(audio)

		transcript = get_text_from_pcm(audio, sample_rate, lang) if raw_pcm else \
		get_text(audio, sample_rate, lang)

		translated = translate(transcript, 'en', lang.split('-')[0])
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

@app.route("/streams")
def streams():
	return send_file('media.html')

@app.route("/<path:filename>")
def file(filename):
	return send_file(filename)

@app.route("/streams/<path:user_dir>/<path:filename>")
def getFile(user_dir, filename):
	return send_from_directory('streams/' + user_dir, filename)

################# SOCKETS #################

class StreamingSocket(Namespace):

	_HASH_LEN = 20

	streamer  = None
	language  = None
	user_hash = None
	user_dir  = None

	def _initialise_streamer(self, url):
		self.streamer = VideoStreamer(url, self.user_dir, self._playlist_ready)

		try:
			self.streamer.start()
		except Exception:
			emit('stream-response', json.dumps({'media':'', 'error':'Streamlink Unavailable!'}))

	def _generate_user_hash(self):
		return ''.join(random.choices(string.ascii_letters + string.digits, k=self._HASH_LEN))

	def on_connect(self):
		new_hash = self._generate_user_hash()

		print("Creating user directory... ", end="")
		new_hash = self._generate_user_hash()

		os.makedirs('streams/' + new_hash)
		self.user_hash = new_hash
		self.user_dir  = 'streams/' + new_hash
		print("Success!")

		print("Connected to client. User hash: " + self.user_hash)

		emit('server-ready')

	def on_disconnect(self):
		self.streamer.stop()

		if os.path.isdir(self.user_dir):
			shutil.rmtree(self.user_dir)

		print("Disconnected from client. User hash: " + self.user_hash)
		self.user_hash = None
		self.user_dir  = None

	def _generate_playlist(self):
		playlist_path = self.user_dir + '/playlist.m3u8'

		print("Generating file: " + playlist_path)

	def _playlist_ready(self):
		playlist_path = self.user_dir + '/playlist.m3u8'
		emit('stream-response', json.dumps({'media':str(LOCAL_URL + playlist_path)}))

	def on_stream(self, data):
		if self.streamer == None:
			self._initialise_streamer(data['url'])
			self._generate_playlist()

		playlist_path = self.user_dir + '/playlist.m3u8'
		master_playlist_path = self.user_dir + '/masterplaylist.m3u8'

		with open(playlist_path, "w") as f:
			f.write("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:20\n#EXT-X-MEDIA-SEQUENCE:0\n")

		with open(master_playlist_path, "w") as masterplaylist:
			masterplaylist.write('#EXTM3U\n')
			masterplaylist.write('#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="English",URI="subtitles.m3u8",LANGUAGE="en"\n')
			masterplaylist.write('#EXT-X-STREAM-INF:BANDWIDTH=1118592,CODECS="mp4a.40.2, SUBTITLES="subs"\n')
			masterplaylist.write('playlist.m3u8')

		subtitle_playlist_path = self.user_dir + "/subtitles.m3u8"
		with open(subtitle_playlist_path, "w") as subtitleplaylist:
			subtitleplaylist.write('#EXTM3U\n')
			subtitleplaylist.write('#EXT-X-TARGETDURATION:20\n')
			subtitleplaylist.write('#EXT-X-VERSION:3\n')
			subtitleplaylist.write('#EXT-X-MEDIA-SEQUENCE:1\n')
			subtitleplaylist.write('#EXTINF:20,\n')
			subtitleplaylist.write('subtitleSegment1.webvtt\n')
			subtitleplaylist.write('#EXT-X-ENDLIST\n')

		with open(self.user_dir + '/subtitleSegment1.webvtt', "w") as f:
			f.write("WEBVTT\n")
			f.write("\n")
			f.write('00:00:00.00-->00:00:10.00 align:start\n')
			f.write('This is a caption\n')

		emit('stream-response', json.dumps({'media':str(LOCAL_URL + master_playlist_path)}))


socketio.on_namespace(StreamingSocket('/streams'))

if __name__ == '__main__':
	socketio.run(app)
