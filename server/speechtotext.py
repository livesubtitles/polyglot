import io
import json
import os
import wave
import struct
import array
import requests
import base64

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from server.translate import *

# Sets up and sends an HTTP request to Google speech-to-text with user credentials
def _send_stt_request_credentials(lang, sample_rate, audiobase64, credentials):
	url = "https://speech.googleapis.com/v1/speech:recognize"
	headers = {'Accept-Encoding': 'UTF-8', 'Content-Type': 'application/json'}

	config = {}
	config['encoding'] = 'LINEAR16'
	config['languageCode'] = lang
	config['sampleRateHertz'] = sample_rate
	config['enableWordTimeOffsets'] = False

	audio = {}
	audio['content'] = audiobase64

	body = {}
	body['config'] = config
	body['audio'] = audio
	body = json.dumps(body)

	http = httplib2.Http()
	http_auth = credentials.authorize(http)
	resp, content = http.request(url, method="POST", headers=headers, body=body)
	print(content.decode('utf-8'))
	return json.loads(content.decode('utf-8'))

# Sets up and sends an HTTP request to Google speech-to-text using our api key
def _send_stt_request(lang, sample_rate, audiobase64):
	apiKey = os.environ.get('APIKEY')
	url = "https://speech.googleapis.com/v1/speech:recognize?key=" + apiKey
	headers = {'Accept-Encoding': 'UTF-8', 'Content-Type': 'application/json'}

	config = {}
	config['encoding'] = 'LINEAR16'
	config['languageCode'] = lang
	config['sampleRateHertz'] = sample_rate
	config['enableWordTimeOffsets'] = False

	audio = {}
	audio['content'] = audiobase64

	body = {}
	body['config'] = config
	body['audio'] = audio
	body = json.dumps(body)

	response = requests.post(url, headers = headers, data = body)
	return response.json()

# Initiates and handles response from speech-to-text API
def _speech_to_text(audio_file, sample_rate, lang, credentials):
		audiobase64 = _convert_to_base64(audio_file)

		url = "https://rumosrucml.execute-api.us-east-2.amazonaws.com/api/transcribe"
		audiores = {}
		audiores['content'] = audiobase64
		body = {}
		body['audio'] = audiores
		body['sample_rate'] = sample_rate
		body['lang'] = lang
		print(body)
		data = json.dumps(body)
		print(data)
		headers = {'content-type': 'application/json'}
		resp = requests.post(url, data=data, headers = headers)
		print(resp.text)
		translated = resp.text

		result = translated

		# if (lang == 'detected'):
		# 		return ""
		#
		# if os.environ.get('MODE') != 'paid':
		# 	json_response = _send_stt_request(lang, sample_rate, audiobase64)
		# else:
		# 	json_response = _send_stt_request_credentials(lang, sample_rate, audiobase64, credentials)
		#
		# try:
		# 		result = json_response['results'][0]['alternatives'][0]['transcript']
		# except KeyError as exc:
		# 		result = ""
		# 		return result
		return result

# Converts audio file to base64 string
def _convert_to_base64(wav_file):
	audio_content = wav_file.getvalue()
	return base64.b64encode(audio_content).decode('ascii')

# Converts PCM data passed by the front end to a wav file required by the API
def _convert_to_wav(pcm_data, sample_rate):
	temp_file = io.BytesIO()
	file = wave.open(temp_file, 'wb')
	file.setframerate(sample_rate)
	file.setnchannels(1)
	file.setsampwidth(2)
	for i in pcm_data:
			floats = array.array('f', [i])
			samples = []
			for sample in floats:
					if (sample < 1 and sample > -1):
							samples.append(int(sample * 32767))
			raw_ints = struct.pack("<%dh" % len(samples), *samples)
			file.writeframes(raw_ints)
	file.close()
	return temp_file


########### PUBLIC FUNCTIONS ###########

# Main speech to text function. Given the wav audio data returns the transcript
def get_text(wav_file, sample_rate, lang, credentials):
		return _speech_to_text(wav_file, sample_rate, lang, credentials)

# Gets subtitle for given audio data
def get_text_from_pcm(pcm_data, sample_rate, lang, credentials):
		wav_file = _convert_to_wav(pcm_data, sample_rate)
		return get_text(wav_file, sample_rate, lang, credentials)

def convert_to_wav(pcm_data, sample_rate):
	return _convert_to_wav(pcm_data, sample_rate)
