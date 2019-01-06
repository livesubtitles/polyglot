import unittest
import sys
import httplib2
import json
import jsonpickle
import string
import random
import os
import shutil
import re
import pytest
import mock
from mock import *

from flask import Flask, request, jsonify, send_from_directory, send_file, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, Namespace, disconnect

from server.translate import test
from pathlib import Path
import server.speechtotext
from server.speechtotext import *
from server.language import *
import server.app
from server.app import *
from server.stream import *
from server.playlist import *
from server.support import isStreamLinkSupported
from server.iptotime import *
from apiclient import discovery
from oauth2client import client



class MockResponse(object):
    def __init__(self, status):
        self.status = status

class AppTest(unittest.TestCase):

    @pytest.fixture
    def client():
        db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
        flaskr.app.config['TESTING'] = True
        client = flaskr.app.test_client()

        with flaskr.app.app_context():
            flaskr.init_db()

        yield client

        os.close(db_fd)
        os.unlink(flaskr.app.config['DATABASE'])

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        pass

    def tearDown(self):
        pass

    def test_index_html(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)

    def test_server_url_is_prod_url(self):
        self.assertEqual(SERVER_URL, HEROKU_URL)

    @patch('server.app.detect_language', return_value="Fr-fr")
    @patch('server.app.get_text', return_value="French chips are good")
    def test_process_with_language_not_set(self, detect_language, get_text):
        with app.test_request_context():
            translated_in_json = server.app.process([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000, '')
            self.assertEqual(json.loads(translated_in_json.get_data().decode("utf-8")), {'lang': 'Fr-fr', 'subtitle': 'French chips are good'})
            self.assertEqual(detect_language.call_count, 1)
            self.assertEqual(get_text.call_count, 1)

    @patch('server.app.detect_language', return_value="Fr-fr")
    @patch('server.app.get_text', return_value="Les frites françaises sont bonnes")
    @patch('server.app.translate', return_value="French chips are good")
    def test_process_with_video_no_language_set(self, detect_language, get_text, translate):
        with app.test_request_context():
            translated_in_json = server.app.process_with_video([-0.9, 0.45, 0, 0.42, -0.32, 0],
                        [-0.9, 0.45, 0, 0.42, -0.32, 0], 2000, '')
            self.assertEqual(json.loads(translated_in_json.get_data().decode("utf-8")),
                            {'lang': 'Fr-fr', 'subtitle': 'French chips are good', 'video': '[-0.9, 0.45, 0, 0.42, -0.32, 0]'})
            self.assertEqual(detect_language.call_count, 1)
            self.assertEqual(get_text.call_count, 1)
            self.assertEqual(translate.call_count, 1)

    def test_initialising_streamer_successfu(self):
        with app.test_request_context():
            with patch.object(server.stream.VideoStreamer,
            'start', return_value='') as mock_method:
                server.app._initialise_streamer("https://www.twitch.tv/valkia")
                self.assertEqual(mock_method.call_count, 1)

    def test_initialising_streamer_failure(self):
        with app.test_request_context():
            with patch.object(server.stream.VideoStreamer, 'start') as mock_method:
                mock_method.side_effect = Exception()
                response = server.app._initialise_streamer("https://www.twitch.tv/valkia")
                self.assertEqual(json.loads(response.get_data().decode("utf-8"))['error'], 'StreamlinkUnavailable ')
                self.assertEqual(mock_method.call_count, 1)

    @patch('server.app.isStreamLinkSupported', return_value="Supported websites")
    def test_supports_html(self, isStreamLinkSupported):
        with app.test_request_context():
            response = self.app.get("/supports")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.get_data().decode("utf-8")), {'answer': 'Supported websites'})

    @patch('server.app.process', return_value=json.dumps({"subtitle": "This is testing", "lang": "Fr-fr"}), status_code=200)
    def test_subtitle_html(self, process):
        with app.test_request_context():
            response = self.app.post("/subtitle", json={'audio': '[-0.9, 0.45, 0, 0.42, -0.32, 0]', 'sampleRate':2000, 'lang':'Fr-fr'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.get_data().decode("utf-8")), {"subtitle": "This is testing", "lang": "Fr-fr"})

    def test_set_language_html(self):
        with app.test_request_context():
            response = self.app.post("/set-language", data="Fr-fr")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data().decode("utf-8"), 'Success')
            self.assertEqual(server.app.language, "Fr-fr")

    @patch('server.app.language', "Fr-fr")
    def test_get_language_html(self):
        with app.test_request_context():
            response = self.app.get("/get-language")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data().decode("utf-8"), "Fr-fr")
            self.assertEqual(server.app.language, "Fr-fr")

    # @patch('server.app.streamer', None)
    # @patch('server.app.process_with_video', return_value=json.dumps({'lang': 'Fr-fr', 'subtitle': 'French chips are good', 'video': '[-0.9, 0.45, 0, 0.42, -0.32, 0]'}), status_code=200)
    # def test_stream_html(self, process_with_video):
    #     with app.test_request_context():
    #         with patch.object(server.stream.VideoStreamer, 'get_data', return_value=([-0.9, 0.45, 0, 0.42, -0.32, 0], [-0.9, 0.45, 0, 0.42, -0.32, 0])) as mock_method1:
    #             with patch.object(server.stream.VideoStreamer, 'get_sample_rate', return_value=2000) as mock_method2:
    #                 response = self.app.post("/stream", json={'lang': 'Fr-fr', 'url': 'https://www.twitch.tv/valkia'})
    #                 self.assertEqual(response.status_code, 200)
    #                 self.assertEqual(json.loads(response.get_data().decode("utf-8")), {'lang': 'Fr-fr', 'subtitle': 'French chips are good', 'video': '[-0.9, 0.45, 0, 0.42, -0.32, 0]'})

    @patch('server.app.send_file', return_value="A html document")
    def test_streams_html(self, send_file):
        with app.test_request_context():
            response = self.app.get("/streams")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data().decode("utf-8"), "A html document")

    @patch('server.app.send_file', return_value="A html document")
    def test_authenticate_html(self, send_file):
        with app.test_request_context():
            response = self.app.get("/authenticate")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data().decode("utf-8"), "A html document")

    @patch('server.app.send_file', return_value="A html document")
    def test_file_html(self, send_file):
        with app.test_request_context():
            response = self.app.get("/media.html")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data().decode("utf-8"), "A html document")

    @patch('server.app.send_file', return_value="A html document")
    def test_pay_html(self, send_file):
        with app.test_request_context():
            response = self.app.get("/pay")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data().decode("utf-8"), "A html document")

    @patch('server.app.send_from_directory', return_value="A html document")
    def test_getFile_from_user_dir_html(self, send_file):
        with app.test_request_context():
            response = self.app.get("streams/user1/document.html")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data().decode("utf-8"), "A html document")

    @patch('server.app.session', dict())
    @patch('server.app.client.credentials_from_clientsecrets_and_code', return_value= MagicMock())
    def test_store_auth_code_html(self, credentials):
        credentials.id_token = {'sub':"user123", 'email':"user123@email.com"}
        with app.test_request_context():
            with patch.object(client.Credentials, 'authorize', return_value="http_auth") as mock_method1:
                with patch.object(httplib2.Http, 'request', return_value=(MockResponse(200), "translated_text".encode('utf-8'))) as mock_method2:
                    response = self.app.post("/storeauthcode", data="auth_code")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.get_data().decode("utf-8"), "")
                    self.assertEqual(credentials.call_count, 1)

    # SOCKETS TESTS
    @patch('server.app.session', dict())
    @patch('server.app.random.choices', return_value="user123")
    def test_socket_on_connect_and_stream(self, random):
        with app.test_request_context():
            request_mock = MagicMock()
            request_mock.remote_addr = "127.0.0.1"
            request_mock.sids = "123456789"
            request_mock.namespace = "123"

            playlist_mock = MagicMock()

            streamer_mock = MagicMock()
            streamer_mock().start.return_value = playlist_mock
            streamer_mock().get_supported_qualities.return_value = ['360p', '480p', '720p']
            streamer_mock().update_sub_language.return_value = "en"

            with patch("server.app.request", request_mock):
                with patch("flask.request", request_mock):
                    with patch('server.app.VideoStreamer', streamer_mock):
                        with patch('server.playlist.HLSPlaylist', playlist_mock):
                            with patch.object(server.playlist.HLSPlaylist, 'get_master', return_value='example/video1') as mock_get_master:
                                streaming_socket = StreamingSocket()
                                streaming_socket.on_connect()
                                streaming_socket.on_stream({'url': "https://www.twitch.tv/valkia", 'lang': "Fr-fr"})
                                streams_folder = Path("streams/user123")

                                self.assertEqual(streams_folder.is_dir(), True)
                                self.assertEqual(random.call_count, 1)
                                self.assertEqual(server.app.session["uid"], "user123")
                                self.assertEqual(server.app.session["ip"], "127.0.0.1")

                                self.assertEqual(streamer_mock().start.call_count, 1)
                                self.assertEqual(streamer_mock().get_supported_qualities.call_count, 1)
                                self.assertEqual(mock_get_master.call_count, 1)

                                streaming_socket.on_language({'sub_lang':'es'})
                                self.assertEqual(streamer_mock().update_sub_language.call_count, 1)


    @patch('server.app.session', dict())
    @patch('server.app.random.choices', return_value="user123")
    def test_socket_disconnect_and_cleanup(self, random):
        with app.test_request_context():
            m = mock.MagicMock()
            m.remote_addr = "127.0.0.1"
            m.sids = "123456789"
            m.namespace = "123"
            with mock.patch("server.app.request", m):
                with mock.patch("flask.request", m):
                    streaming_socket = StreamingSocket()
                    streaming_socket.on_connect()
                    streams_folder = Path("streams/user123")

                    self.assertEqual(streams_folder.is_dir(), True)
                    self.assertEqual(random.call_count, 1)
                    self.assertEqual(server.app.session["uid"], "user123")
                    self.assertEqual(server.app.session["ip"], "127.0.0.1")

                    streaming_socket.on_disconnect()
                    self.assertEqual(streams_folder.is_dir(), False)
                    self.assertEqual("127.0.0.1" in streaming_socket.streamers, False)

    # @patch('server.app.session', dict())
    # @patch('server.app.random.choices', return_value="user123")
    # def test_socket_disconnect_and_cleanup(self, random):
    #     with app.test_request_context():
    #         m = mock.MagicMock()
    #         m.remote_addr = "127.0.0.1"
    #         m.sids = "123456789"
    #         m.namespace = "123"
    #         with mock.patch("server.app.request", m):
    #             with mock.patch("flask.request", m):
    #                 streaming_socket = StreamingSocket()
    #                 streaming_socket.on_connect()
    #                 streams_folder = Path("streams/user123")
    #
    #                 self.assertEqual(streams_folder.is_dir(), True)
    #                 self.assertEqual(random.call_count, 1)
    #                 self.assertEqual(server.app.session["uid"], "user123")
    #                 self.assertEqual(server.app.session["ip"], "127.0.0.1")
    #
    #                 streaming_socket.on_language({'sub_lang':'Fr-fr'})
    #                 self.assertEqual(streams_folder.is_dir(), False)
    #                 self.assertEqual("127.0.0.1" in streaming_socket.streamers, False)

if __name__ == '__main__':
    unittest.main()
