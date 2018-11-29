import httplib2
import json
import jsonpickle
import string
import random
import os
import shutil
import re

from flask import Flask, request, jsonify, send_from_directory, send_file, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit, Namespace

from server.translate import test
from server.speechtotext import *
from server.language import *
from server.stream import *
from server.support import isStreamLinkSupported
from apiclient import discovery
from oauth2client import client

app = Flask(__name__)
# login_manager = LoginManager()
# login_manager.init_app(app)
CORS(app)
app.secret_key = b'\xc4Q\x8e\x10b\xafy\x10\xc0i\xb5G\x08{]\xee'
socketio = SocketIO(app)
streamer = None
language = ""

LOCAL_URL  = 'http://localhost:8000/'
HEROKU_URL = 'https://polyglot-livesubtitles.herokuapp.com/'
TEST_URL = 'https://test-polyglot.herokuapp.com/'
SERVER_URL = TEST_URL

MASTER_STUB = '#EXTM3U\n#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="English",URI="subtitles.m3u8",LANGUAGE="en"\n#EXT-X-STREAM-INF:BANDWIDTH=200000,RESOLUTION=480x360,SUBTITLES="subs"\nplaylist.m3u8\n'
PLAYLIST_STUB = '#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:20\n#EXT-X-MEDIA-SEQUENCE:0\n'

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

def _generate_user_hash():
	return ''.join(random.choices(string.ascii_letters + string.digits, k=20))

################## LOGIN MANAGER ##################
# @login_manager.user_loader
# def load_user(user_id):
#     return User.get(user_id)

 ################# REST ENDPOINTS #################

@app.route("/")
def hello():
	return "Polyglot - Live Subtitles - ICL"

@app.route("/supports", methods=['GET'])
def supportsStreamlink():
	url = request.args.get("web")
	return json.dumps(isStreamLinkSupported(url));

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

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

@app.route("/streams")
def streams():
	print(session['userid'])
	credentials = jsonpickle.loads(session['credentials'])
	if not 'email' in session:
		return "You are not logged in"
	return send_file('media.html')

@app.route("/authenticate")
def oauth():
	return send_file('oauth.html')

@app.route("/<path:filename>")
def file(filename):
	return send_file(filename)

@app.route("/streams/<path:user_dir>/<path:filename>")
def getFile(user_dir, filename):
	return send_from_directory('streams/' + user_dir, filename)

@app.route("/storeauthcode", methods=['POST'])
def get_user_access_token_google():
	auth_code = str(request.data).split("\'")[1]
	# If this request does not have `X-Requested-With` header, this could be a CSRF
	# Set path to the Web application client_secret_*.json file you downloaded from the
	# Google API Console: https://console.developers.google.com/apis/credentials
	CLIENT_SECRET_FILE = 'client_secret_1070969009500-4674ntngjh3dvlbcvoer0r4c7hao04dh.apps.googleusercontent.com.json'

	# Exchange auth code for access token, refresh token, and ID token
	credentials = client.credentials_from_clientsecrets_and_code(
		CLIENT_SECRET_FILE,
		['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
		auth_code)

	# Call Google API
	http = httplib2.Http()
	http_auth = credentials.authorize(http)
	resp, content = http.request(
		'https://www.googleapis.com/language/translate/v2/?q=voiture&target=en&source=fr')
	print(resp.status)
	print(content.decode('utf-8'))

	# Get profile info from ID token
	userid = credentials.id_token['sub']
	email = credentials.id_token['email']
	session['email'] = email
	session['userid'] = userid
	session['credentials'] = jsonpickle.dumps(credentials)
	print(userid)
	print(email)
	return ""

@app.route('/logout')
def logout():
	# remove the username from the session if it's there
	session.pop('email', None)
	session.pop('userid', None)
	return redirect(url_for('index'))

################# SOCKETS #################

class StreamingSocket(Namespace):

	_HASH_LEN = 20

	streamers = {}

	def _initialise_new_streamer(self, url, user):
		credentials = jsonpickle.loads(session['credentials'])
		streamer = VideoStreamer(url, 'streams/' + user, credentials)
		try:
			streamer.start()
			self.streamers[user] = streamer
		except Exception as exe:
			emit('stream-response', json.dumps({'media':'', 'error':exe}))

	def _generate_user_hash(self):
		return ''.join(random.choices(string.ascii_letters + string.digits, k=self._HASH_LEN))

	def on_connect(self):
		print("Creating user details... ", end="")
		new_hash = self._generate_user_hash()
		session['uid'] = new_hash
		os.makedirs('streams/' + new_hash)
		print("Success!")

		print("Connected to client. User hash: " + new_hash)
		emit('server-ready')

	def on_disconnect(self):
		user = session['uid']
		print("Disconneting from user: " + user)
		print("Stopping worker...", end="")
		self.streamers[user].stop()
		self.streamers.pop(user)
		print("Success!")

		print("Removing user files at " + 'streams/' + user + "...", end="")
		if os.path.isdir('streams/' + user):
			shutil.rmtree('streams/' + user)
			print("Success!")
		else:
			print("!!! Not found !!!")

	def _generate_playlists(self, user):
		masterplaylist_path = 'streams/' + user + '/masterplaylist.m3u8'
		playlist_path = 'streams/' + user + '/playlist.m3u8'
		subtitle_path = 'streams/' + user + '/subtitles.m3u8'

		with open(masterplaylist_path, 'w') as f:
			f.write(MASTER_STUB)

		with open(playlist_path, 'w') as f:
			f.write(PLAYLIST_STUB)

		with open(subtitle_path, 'w') as f:
			f.write(PLAYLIST_STUB)

		return masterplaylist_path

	def on_stream(self, data):
		user = session['uid']
		self._initialise_new_streamer(data['url'], user)
		master_path = self._generate_playlists(user);

		emit('stream-response', json.dumps({'media':str(SERVER_URL + master_path)}))

socketio.on_namespace(StreamingSocket('/streams'))

if __name__ == '__main__':
	socketio.run(app)
