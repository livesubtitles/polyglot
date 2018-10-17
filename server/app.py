from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

@app.route("/")
def hello():
    return "Polyglot - Live Subtitles - ICL"

@app.route("/pablo")
def pablo():
    return "GOROSTIAGAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

@socketio.on('connect')
def test_connect():
    print("Connected.")
    emit('connection', {'data': 'Connected'})

@socketio.on("audioprocess")
def audioprocess(payload):
    print("Python payload " + str( payload ))

if __name__ == '__main__':
    socketio.run(app)
