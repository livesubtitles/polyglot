from flask import Flask
from flask_cors import CORS
from flask import request
from speechtotext import *
import json
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
CORS(app, resources={r"/subtitle": {"origins": "*"}})
socketio = SocketIO(app)
connection_lock = threading.Lock();
connections = {}
next_connection_id = 0

@app.route("/")
def hello():
    return "Polyglot - Live Subtitles - ICL"

@app.route("/subtitle", methods=['POST'])
def subtitle():
    request_body = json.loads(request.data)
    return "{\"subtitle\":\"" + get_subtitle(request_body['audio'], request_body['sampleRate']) + "\"}"

# Socket connection
@socketio.on('connect')
def connect():
    print("New websocket connection.")
    # Generate a new audio stream for this specific connection
    connection_lock.acquire()
    connection_id = next_connection_id
    connections[connection_id] = AudioStreamer()
    next_connection_id = next_connection_id += 1
    connection_lock.release()
    emit('connection', {'data': 'Connected', "connection_id": connection_id })

# TODO: Implement socket disconnection on backend and frontend

@socketio.on("audioprocess")
def audioprocess(payload):
    connection_id = payload["connection_id"]
    print( "Received payload from connection_id: " + connection_id )
    connection_lock.acquire()
    audiostreamer = connections[connection_id]
    connection_lock.release()
    audiostreamer.received_audio_buffer( payload["channelData"] )

    print("Python payload " + str( payload ))

if __name__ == '__main__':
    socketio.run(app)
