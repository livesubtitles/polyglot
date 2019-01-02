import io
import json
import os
import wave
import struct
import array
import requests
import base64
from zope.interface import Interface, implementer
from server.adapter import *
from server.translate import *
from server.speechtotext import *

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

@implementer(TranscriptionService)
class googleTranscriptionService(object):

    def __init__(self):
        pass

    # Sets up and sends an HTTP request to Google speech-to-text with user credentials
    # def _send_stt_request_credentials(self, lang, sample_rate, audiobase64, credentials):
    # 	url = "https://speech.googleapis.com/v1/speech:recognize"
    # 	headers = {'Accept-Encoding': 'UTF-8', 'Content-Type': 'application/json'}
    #
    # 	config = {}
    # 	config['encoding'] = 'LINEAR16'
    # 	config['languageCode'] = lang
    # 	config['sampleRateHertz'] = sample_rate
    # 	config['enableWordTimeOffsets'] = False
    #
    # 	audio = {}
    # 	audio['content'] = audiobase64
    #
    # 	body = {}
    # 	body['config'] = config
    # 	body['audio'] = audio
    # 	body = json.dumps(body)
    #
    # 	http = httplib2.Http()
    # 	http_auth = credentials.authorize(http)
    # 	resp, content = http.request(url, method="POST", headers=headers, body=body)
    # 	print(content.decode('utf-8'))
    # 	return json.loads(content.decode('utf-8'))
    #
    # # Sets up and sends an HTTP request to Google speech-to-text using our api key
    # def _send_stt_request(self, lang, sample_rate, audiobase64):
    # 	apiKey = os.environ.get('APIKEY')
    # 	url = "https://speech.googleapis.com/v1/speech:recognize?key=" + apiKey
    # 	headers = {'Accept-Encoding': 'UTF-8', 'Content-Type': 'application/json'}
    #
    # 	config = {}
    # 	config['encoding'] = 'LINEAR16'
    # 	config['languageCode'] = lang
    # 	config['sampleRateHertz'] = sample_rate
    # 	config['enableWordTimeOffsets'] = False
    #
    # 	audio = {}
    # 	audio['content'] = audiobase64
    #
    # 	body = {}
    # 	body['config'] = config
    # 	body['audio'] = audio
    # 	body = json.dumps(body)
    #
    # 	response = requests.post(url, headers = headers, data = body)
    # 	return response.json()

    # Initiates and handles response from speech-to-text API
    def _speech_to_text(self, audiobase64, sample_rate, lang, credentials, sub_lang):
        url = "https://rumosrucml.execute-api.us-east-2.amazonaws.com/api/transcribe"
        audiores = {}
        audiores['content'] = audiobase64
        body = {}
        body['audio'] = audiores
        body['sample_rate'] = sample_rate
        body['sub_lang'] = sub_lang
        body['lang'] = lang
        print(body)
        data = json.dumps(body)
        print(data)
        headers = {'content-type': 'application/json'}
        resp = requests.post(url, data=data, headers = headers)
        print(resp.text)
        translated = resp.text
        return translated
