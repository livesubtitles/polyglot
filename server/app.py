from flask import Flask
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
socketio = SocketIO(app)
connection_lock = threading.Lock();
connections = {}
next_connection_id = 0

@app.route("/")
def hello():
    return "Polyglot - Live Subtitles - ICL"

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
