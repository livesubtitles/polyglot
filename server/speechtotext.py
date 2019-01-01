import io
import json
import os
import wave
import struct
import array
import requests
import base64
from server.translate import *

# Imports specific adapter file
from server.transcriptionservices.google import *

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

transcriptionservice = googleTranscriptionService()

def _speech_to_text(audio_file, sample_rate, lang, credentials):
	audiobase64 = _convert_to_base64(audio_file)
	return transcriptionservice._speech_to_text(audiobase64, sample_rate, lang, credentials)

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
def get_text(wav_file, sample_rate, lang, credentials, sub_lang):
		return _speech_to_text(wav_file, sample_rate, lang, credentials, sub_lang)

# Gets subtitle for given audio data
def get_text_from_pcm(pcm_data, sample_rate, lang, credentials, sub_lang):
		wav_file = _convert_to_wav(pcm_data, sample_rate)
		return get_text(wav_file, sample_rate, lang, credentials, sub_lang)

def convert_to_wav(pcm_data, sample_rate):
	return _convert_to_wav(pcm_data, sample_rate)
