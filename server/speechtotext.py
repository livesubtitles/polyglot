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
from translate import *

# Sends request to Speech-to-Text API
def speech_to_text(audio_file, sample_rate, lang):
    apiKey = os.environ.get('APIKEY')
    audiobase64 = convert_to_base64(audio_file)
    # Create request
    url = "https://speech.googleapis.com/v1/speech:recognize?key=" + apiKey
    headers = {'Accept-Encoding': 'UTF-8', 'Content-Type': 'application/json'}
    body = {}
    config = {}
    config['encoding'] = 'LINEAR16'
    config['languageCode'] = lang
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
def get_subtitle(pcm_data, sample_rate, lang):
    wav_file = convert_to_wav(pcm_data, sample_rate)
    transcript = speech_to_text(wav_file, sample_rate, lang)
    return translate(transcript, 'en', lang.split('-')[0])




import urllib.parse, time

headers = {
    'Ocp-Apim-Subscription-Key': '1cf34f34513d4e1d8568c5d2a4b81fec'
}

form_data = {'file': open('/Users/hanglili/Downloads/test9.wav', 'rb')}

params = urllib.parse.urlencode({
    # 'name': 'test.wav',
    'language': 'auto',
    # 'privacy': 'Private'
})

try:
    url = 'https://api.videoindexer.ai/trial/Accounts/82a02c9c-734d-48d1-99e7-4e3c0f523904/Videos?accessToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJBY2NvdW50SWQiOiI4MmEwMmM5Yy03MzRkLTQ4ZDEtOTllNy00ZTNjMGY1MjM5MDQiLCJBbGxvd0VkaXQiOiJUcnVlIiwiRXh0ZXJuYWxVc2VySWQiOiIwMGZlY2ZjZTYzOTliZDYxIiwiVXNlclR5cGUiOiJNaWNyb3NvZnQiLCJpc3MiOiJodHRwczovL3d3dy52aWRlb2luZGV4ZXIuYWkvIiwiYXVkIjoiaHR0cHM6Ly93d3cudmlkZW9pbmRleGVyLmFpLyIsImV4cCI6MTU0MDY1MjQxNCwibmJmIjoxNTQwNjQ4NTE0fQ.FnzRT7kJ3eQCF9iurt6IZbNBU-ozIAXVBEUXUmbJHR8&name=test9'
    print ("HELLO!!!!!!!!!!")
    r = requests.post(url, params=params, files=form_data, headers=headers)
    print(r.url)
    print(json.dumps(r.json(), indent=2))
    print ("BYE!!!!!!!!!!!!!!")
    videoId = (r.json())['id']
    print ("The videoId is " + videoId)
    sourceLang = None
    while (sourceLang == None):
        time.sleep(5)
        url2 = 'https://api.videoindexer.ai/trial/Accounts/82a02c9c-734d-48d1-99e7-4e3c0f523904/Videos/{videoId}/Index?accessToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJBY2NvdW50SWQiOiI4MmEwMmM5Yy03MzRkLTQ4ZDEtOTllNy00ZTNjMGY1MjM5MDQiLCJBbGxvd0VkaXQiOiJUcnVlIiwiRXh0ZXJuYWxVc2VySWQiOiIwMGZlY2ZjZTYzOTliZDYxIiwiVXNlclR5cGUiOiJNaWNyb3NvZnQiLCJpc3MiOiJodHRwczovL3d3dy52aWRlb2luZGV4ZXIuYWkvIiwiYXVkIjoiaHR0cHM6Ly93d3cudmlkZW9pbmRleGVyLmFpLyIsImV4cCI6MTU0MDY1MjQxNCwibmJmIjoxNTQwNjQ4NTE0fQ.FnzRT7kJ3eQCF9iurt6IZbNBU-ozIAXVBEUXUmbJHR8'
        r = requests.get(url, headers=headers)
        sourceLang = (r.json())['results'][0]['sourceLanguage']
        print ("The source language is " , sourceLang)
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))


# import http.client, urllib.request, urllib.parse, urllib.error, base64
#
# headers = {
#     # Request headers
# }

# form_data = {'file': open('/Users/hanglili/Downloads/test.wav', 'rb')}

# form_data = open('/Users/hanglili/Downloads/test.wav', 'rb')
#
# params = urllib.parse.urlencode({
#     # Request parameters
#     # 'description': '{string}',
#     # 'partition': '{string}',
#     # 'externalId': '{string}',
#     # 'callbackUrl': '{string}',
#     # 'metadata': '{string}',
#     'language': 'auto',
#     # 'fileName': '{string}',
#     # 'indexingPreset': '{string}',
#     # 'streamingPreset': 'Default',
#     # 'linguisticModelId': '{string}',
#     # 'privacy': '{string}',
#     # 'externalUrl': '{string}',
#     # 'assetId': '{string}',
#     # 'priority': '{string}',
# })

# try:
#     conn = http.client.HTTPSConnection('api.videoindexer.ai')
#     conn.request("POST", "/trial/Accounts/82a02c9c-734d-48d1-99e7-4e3c0f523904/Videos?accessToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJBY2NvdW50SWQiOiI4MmEwMmM5Yy03MzRkLTQ4ZDEtOTllNy00ZTNjMGY1MjM5MDQiLCJBbGxvd0VkaXQiOiJUcnVlIiwiRXh0ZXJuYWxVc2VySWQiOiIwMGZlY2ZjZTYzOTliZDYxIiwiVXNlclR5cGUiOiJNaWNyb3NvZnQiLCJpc3MiOiJodHRwczovL3d3dy52aWRlb2luZGV4ZXIuYWkvIiwiYXVkIjoiaHR0cHM6Ly93d3cudmlkZW9pbmRleGVyLmFpLyIsImV4cCI6MTU0MDY1MjQxNCwibmJmIjoxNTQwNjQ4NTE0fQ.FnzRT7kJ3eQCF9iurt6IZbNBU-ozIAXVBEUXUmbJHR8&name=test&%s" % params, form_data, headers)
#     response = conn.getresponse()
#     data = response.read()
#     print(data)
#     conn.close()
# except Exception as e:
#     print("[Errno {0}] {1}".format(e.errno, e.strerror))

####################################
