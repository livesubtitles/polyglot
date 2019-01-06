import httplib2
import json
import jsonpickle
import string
import random
import os
import shutil
import re

from flask import Flask, request, jsonify, send_from_directory, send_file, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, Namespace, disconnect

from server.translate import test
from server.speechtotext import *
from server.language import *
from server.stream import *
from server.playlist import *
from server.support import isStreamLinkSupported
from server.iptotime import *
from apiclient import discovery
from oauth2client import client

app = Flask(__name__)
CORS(app)
app.secret_key = b'\xc4Q\x8e\x10b\xafy\x10\xc0i\xb5G\x08{]\xee'
socketio = SocketIO(app)
streamer = None
language = ""
credentials = None
ip_to_time = IpToTimeMap()
client_sids = {}

LOCAL_URL  = 'http://localhost:8000/'
HEROKU_URL = 'https://polyglot-livesubtitles.herokuapp.com/'
SERVER_URL = HEROKU_URL

# Main pipeline. Will return the JSON response with the translated text.
def process(audio, sample_rate, lang, raw_pcm=False, sub_lang="En-en"):
    if lang == '':
        lang = detect_language(convert_to_wav(audio, sample_rate))

    transcript = get_text_from_pcm(audio, sample_rate,
                     lang, None, sub_lang) if raw_pcm else get_text(audio, sample_rate, lang, None, sub_lang)
    #TODO: Rename variables
    translated = translate(transcript, 'en', lang.split('-')[0], session['credentials'] if 'credentials' in session else None)
    return jsonify(subtitle=translated, lang=lang)

def process_with_video(video, audio, sample_rate, lang):
    if lang == '':
    #TODO: Move the split into the detect_language function
        lang = detect_language(audio)

    transcript = get_text(audio, sample_rate, lang, credentials, "En-en")
    translated = translate(transcript, 'en', lang.split('-')[0], session['credentials'] if 'credentials' in session else None)

    return jsonify(video=jsonpickle.encode(video), subtitle=translated, lang=lang)

def _initialise_streamer(url):
    global streamer
    global ip_to_time

    streamer = VideoStreamer(url, language, None, credentials)

    try:
        streamer.start()
    except Exception:
        return _error_response( "StreamlinkUnavailable ")

def _error_response(error):
    return jsonify(subtitle="", lang="", error=error)

def _generate_user_hash():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))

 ################# REST ENDPOINTS #################

@app.route("/")
def hello():
    return "Polyglot - Live Subtitles - ICL"

@app.route("/supports", methods=['GET'])
def supportsStreamlink():
    url = request.args.get("web")
    return jsonify(answer=isStreamLinkSupported(url,  "supported_websites"));

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

# @app.route("/stream", methods=['POST'])
# def stream():
#   global streamer
#
#   if streamer == None:
#       _initialise_streamer(json.loads(request.data)['url'])
#
#   lang = json.loads(request.data)['lang']
#   (video, audio) = streamer.get_data()
#   sample_rate    = streamer.get_sample_rate()
#
#   return process_with_video(video, audio, sample_rate, lang)

@app.route("/translate-test")
def dummyTranslate():
    return test()

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add("Access-Control-Allow-Credentials", "true")
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Access-Control-Allow-Headers, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers')
  response.headers.add('Access-Control-Allow-Methods', 'GET,HEAD,PUT,POST,DELETE,OPTIONS')
  response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
  response.headers.add('Pragma', 'no-cache')
  response.headers.add('Expires', '0')
  response.headers.add('Cache-Control', 'public, max-age=0')
  return response

@app.route("/streams")
def streams():
    return send_file('media.html')

@app.route("/authenticate")
def oauth():
    return send_file('oauth.html')

@app.route("/<path:filename>")
def file(filename):
    return send_file(filename)

@app.route("/pay")
def pay():
    return send_file('pay.html')

@app.route("/streams/<path:user_dir>/<path:filename>")
def getFile(user_dir, filename):
    return send_from_directory('streams/' + user_dir, filename)

@app.route("/storeauthcode", methods=['POST'])
def get_user_access_token_google():
    global credentials
    print(request.data)
    auth_code = str(request.data).split("\'")[1]
    print(auth_code)
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

    # # Get profile info from ID token
    userid = credentials.id_token['sub']
    email = credentials.id_token['email']
    session['email'] = email
    session['userid'] = userid
    # session['credentials'] = jsonpickle.dumps(credentials)
    # if not 'credentials' in session:
    #   print("Credentials not saved to session")
    # session.modified = True
    print(userid)
    print(email)
    return jsonify(email=email)

################# SOCKETS #################

class StreamingSocket(Namespace):

    _HASH_LEN = 20

    streamers = {}
    global credentials
    global ip_to_time

    def _generate_user_hash(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=self._HASH_LEN))

    def on_connect(self):
        print("Creating user details... ", end="")
        new_hash = self._generate_user_hash()
        print ("The new hash is", new_hash)

        session['uid'] = new_hash
        os.makedirs('streams/' + new_hash)
        print("Success!")

        print("Checking IP for access...", end="")
        ip_address = request.remote_addr
        print("IP address is: ", request.remote_addr + "...", end="")
        session['ip'] = ip_address
        if ip_to_time.is_in(ip_address):
            time = ip_to_time.get_time(ip_address)
            if time >= 3600:
                os.environ["MODE"] = 'paid'
                emit('login-required')
        else:
            ip_to_time.store_time(ip_address, 0)
        print("Success!")

        client_sids[new_hash] = request.sid

        print("Connected to client. User hash: " + new_hash)
        emit('server-ready')

    def on_disconnect(self):
        user = session['uid']
        print("Disconnecting from user: " + user)
        print("Stopping worker...")
        if user in self.streamers:
            self.streamers[user].stop()
            self.streamers.pop(user)
        print("Worker Stopped! Cleaning up...")

        self._cleanup(user)

    def _cleanup(self, user):
        user_path = 'streams/' + user

        print("Removing user files at " + user_path + "...", end="")
        if os.path.isdir(user_path):
            shutil.rmtree(user_path)
            print("Success!")
        else:
            print("!!! Not found !!!")

        print("~~~ Ready ~~~")

    def on_language(self, data):
        user = session['uid']
        new_language = data['sub_lang']

        self.streamers[user].update_sub_language(new_language)

    def on_timeupdate(self, data):
        print("Time update for ip address: {}".format(request.remote_addr))
        print("Time interval in seconds: {}".format(data["interval_seconds"]))

        ip_address = request.remote_addr

        if ip_to_time.is_in(ip_address):
            time = ip_to_time.get_time(ip_address)
            ip_to_time.store_time(ip_address, time + data["interval_seconds"])
        else:
            ip_to_time.store_time(ip_address, data["interval_seconds"])


    def on_quality(self, data):
        user = session['uid']
        new_quality = data['quality']

        new_playlist = self.streamers[user].update_quality(new_quality)

        media_url = str(SERVER_URL + new_playlist.get_master())
        emit('stream-response', json.dumps({'media':media_url}))

    def on_stream(self, data):
        user = session['uid']

        self._progress_update(user)

        print("Creating VideoStreamer for URL: " + data['url'])

        if not 'credentials' in session:
            print("Credentials not saved to session")
        # credentials = jsonpickle.loads(session['credentials'])
        streamer = VideoStreamer(data['url'], data['lang'], user, credentials)

        try:
            playlist = streamer.start(self._progress_update)
        except Exception as exe:
            print("VideoStreamer raised an exception: " + str(exe))
            emit('streamlink-error')
            disconnect()
            return

        self.streamers[user] = streamer

        self._progress_update(user)

        media_url = str(SERVER_URL + playlist.get_master())
        print ("********The master url is", media_url)
        supported_qualities = streamer.get_supported_qualities()
        print ("********The supported qualities are", supported_qualities)
        emit('stream-response', json.dumps({'media':media_url, 'qualities':supported_qualities}))

    def _progress_update(self, user):
        with app.app_context():
            emit('progress', json.dumps({'progress':3}), room=client_sids[user])

    def _check_time_limit(self, user):
        emit('login-required', room=client_sids[user])


socketio.on_namespace(StreamingSocket('/streams'))

if __name__ == '__main__':
    socketio.run(app)
