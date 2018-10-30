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
import random
# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from server.translate import *


# Sends request to Speech-to-Text API
def speech_to_text(audio_file, sample_rate, lang):
    apiKey = os.environ.get('APIKEY')
    audiobase64 = convert_to_base64(audio_file)
    if (lang == 'detected'):
        return ""
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
    try:
        res = decoded_response['results'][0]['alternatives'][0]['transcript']
        print(res)
    except KeyError as exc:
        print(exc)
        res = ""
    return res

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
    if (lang == ''):
        lang = detect_language(wav_file)
    transcript = speech_to_text(wav_file, sample_rate, lang)
    return "{\"subtitle\":\"" + translate(transcript, 'en', lang.split('-')[0]) + "\", \"lang\":\""+lang+"\"}"

def get_subtitle_with_wav(wav_file, sample_rate, lang):
    if (lang == ''):
        lang = detect_language(wav_file)
    transcript = speech_to_text(wav_file, sample_rate, lang)
    return "{\"subtitle\":\"" + translate(transcript, 'en', lang.split('-')[0]) + "\", \"lang\":\""+lang+"\"}"
# Detects language spoken using Microsoft API
def detect_language(audio_file):
    microsoftKey = os.environ.get('MICROSOFTKEY')
    microsoftId = os.environ.get('MICROSOFTID')
    headers = {
        'Ocp-Apim-Subscription-Key': microsoftKey
    }

    url = 'https://api.videoindexer.ai/auth/trial/Accounts/' + microsoftId + '/AccessToken?allowEdit=true'
    response = requests.get(url, headers=headers)
    access_token = response.text.split("\"")[1]

    form_data = {'file': audio_file.getvalue()}

    params = urllib.parse.urlencode({
        'language': 'auto',
    })

    try:
        url = 'https://api.videoindexer.ai/trial/Accounts/'+ microsoftId + '/Videos?accessToken=' + access_token + '&name=test' + str(random.randint(1, 10))
        r = requests.post(url, params=params, files=form_data, headers=headers)
        print(r.url)
        print(json.dumps(r.json(), indent=2))
        video_id = (r.json())['id']
        print ("The videoId is " + video_id)
        source_lang = None
        while(source_lang == None):
            print("HERE")
            time.sleep(2)
            print("HERE TOO")
            url2 = 'https://api.videoindexer.ai/trial/Accounts/723619e4-3df6-4cef-b28b-411d0c114b48/Videos/' + video_id +'/Index?accessToken=' + access_token
            r = requests.get(url2, headers=headers)
            print(r.json())
            source_lang = (r.json())['videos'][0]['insights']['sourceLanguage']
            print ("The source language is " , source_lang)
        return source_lang
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
