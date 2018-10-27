import io
import json
import os
import wave
import struct
import array
import requests
import base64
import urllib.parse
import time
# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from translate import *

is_first = True
detected_lang = ""

# Sends request to Speech-to-Text API
def speech_to_text(audio_file, sample_rate):
    global is_first
    global detected_lang
    apiKey = os.environ.get('APIKEY')
    audiobase64 = convert_to_base64(audio_file)
    if (is_first):
        is_first = False
        detected_lang = detect_language(audio_file)
    # Create request
    url = "https://speech.googleapis.com/v1/speech:recognize?key=" + apiKey
    headers = {'Accept-Encoding': 'UTF-8', 'Content-Type': 'application/json'}
    body = {}
    config = {}
    config['encoding'] = 'LINEAR16'
    config['languageCode'] = detected_lang
    config['sampleRateHertz'] = sample_rate
    config['enableWordTimeOffsets'] = False
    config['enableAutomaticPunctuation'] = True
    body['config'] = config
    audio = {}
    audio['content'] = audiobase64
    body['audio'] = audio
    body = json.dumps(body)
    response = requests.post(url, headers = headers, data = body)
    # Handle response
    decoded_response = response.json()
    print(decoded_response['results'][0]['alternatives'][0]['transcript'])
    return decoded_response['results'][0]['alternatives'][0]['transcript']

# Converts audio file to base64 string
def convert_to_base64(wav_file):
  audio_content = wav_file.getvalue()
  return base64.b64encode(audio_content).decode('ascii')

# Converts PCM data passed by the front end to a wav file required by the API
def convert_to_wav(pcm_data, sample_rate):
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

# Gets subtitle for given audio data
def get_subtitle(pcm_data, sample_rate):
    global detected_lang
    wav_file = convert_to_wav(pcm_data, sample_rate)
    transcript = speech_to_text(wav_file, sample_rate)
    return translate(transcript, 'en', detected_lang.split('-')[0])

# Detects language spoken using Microsoft API
def detect_language(audio_file):
    headers = {
        'Ocp-Apim-Subscription-Key': '1cf34f34513d4e1d8568c5d2a4b81fec'
    }

    form_data = {'file': audio_file.getvalue()}

    params = urllib.parse.urlencode({
        'language': 'auto',
    })

    try:
        url = 'https://api.videoindexer.ai/trial/Accounts/723619e4-3df6-4cef-b28b-411d0c114b48/Videos?accessToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJBY2NvdW50SWQiOiI3MjM2MTllNC0zZGY2LTRjZWYtYjI4Yi00MTFkMGMxMTRiNDgiLCJBbGxvd0VkaXQiOiJUcnVlIiwiRXh0ZXJuYWxVc2VySWQiOiIxMTY0MTg1ODgwNzc5NzY1NTYwNzciLCJVc2VyVHlwZSI6Ikdvb2dsZSIsImlzcyI6Imh0dHBzOi8vd3d3LnZpZGVvaW5kZXhlci5haS8iLCJhdWQiOiJodHRwczovL3d3dy52aWRlb2luZGV4ZXIuYWkvIiwiZXhwIjoxNTQwNjU2NDEyLCJuYmYiOjE1NDA2NTI1MTJ9.7U0pocuUFY1OsbTpxahpq7XYxeONGMNOa1wyPss3jqU&name=test'
        r = requests.post(url, params=params, files=form_data, headers=headers)
        print(r.url)
        print(json.dumps(r.json(), indent=2))
        video_id = (r.json())['id']
        print ("The videoId is " + video_id)
        source_lang = None
        print("HERE")
        # while (source_lang == None):
        time.sleep(15)
        print("HERE TOO")
        url2 = 'https://api.videoindexer.ai/trial/Accounts/723619e4-3df6-4cef-b28b-411d0c114b48/Videos/{video_id}/Index?accessToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJBY2NvdW50SWQiOiI3MjM2MTllNC0zZGY2LTRjZWYtYjI4Yi00MTFkMGMxMTRiNDgiLCJBbGxvd0VkaXQiOiJUcnVlIiwiRXh0ZXJuYWxVc2VySWQiOiIxMTY0MTg1ODgwNzc5NzY1NTYwNzciLCJVc2VyVHlwZSI6Ikdvb2dsZSIsImlzcyI6Imh0dHBzOi8vd3d3LnZpZGVvaW5kZXhlci5haS8iLCJhdWQiOiJodHRwczovL3d3dy52aWRlb2luZGV4ZXIuYWkvIiwiZXhwIjoxNTQwNjU2NDEyLCJuYmYiOjE1NDA2NTI1MTJ9.7U0pocuUFY1OsbTpxahpq7XYxeONGMNOa1wyPss3jqU'
        r = requests.get(url, headers=headers)
        source_lang = (r.json())['results'][0]['sourceLanguage']
        print ("The source language is " , source_lang)
        return source_lang
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
