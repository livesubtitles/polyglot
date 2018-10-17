import io
import json
import os
import wave
import struct
import array
import requests
import base64
# Imports the Google Cloud client library
from google.cloud.speech import types
from translate import *

# Sends request to Speech-to-Text API
def speech_to_text(audio_file, sample_rate, audiostreamer):
    apiKey = os.environ.get('APIKEY')


    client = audiostreamer.client
    print("IN SPEECH TO TEXT")
    with audiostreamer as stream:
        audio_generator = stream.generator()
        requests = ( types.StreamingRecognizeRequest( audio_content=content )
                    for content in audio_generator )
        responses = client.streaming_recognize( stream.streaming_config, requests )
        print( responses )
        for response in responses:
            print("RESPONSES")
            print(response)

    return "J'aime le fromage."





    audiobase64 = "" + convert_to_base64(audio_file)
    # Create request
    url = "https://speech.googleapis.com/v1/speech:recognize?key=" + apiKey
    headers = {'Accept-Encoding': 'UTF-8', 'Content-Type': 'application/json'}
    body = {}
    config = {}
    config['encoding'] = 'LINEAR16'
    config['languageCode'] = 'fr-FR'
    config['sampleRateHertz'] = sample_rate
    config['enableWordTimeOffsets'] = False
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
  sample_rate = int(sample_rate)
  temp_file = io.BytesIO()
  file = wave.open(temp_file, 'wb')
  file.setframerate(sample_rate)
  file.setnchannels(1)
  file.setsampwidth(2)
  for i in pcm_data:
      i = float(i)
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
def get_subtitle(pcm_data, sample_rate, audiostreamer):
    #print(pcm_data)
    wav_file = convert_to_wav(pcm_data, sample_rate)
    transcript = speech_to_text(wav_file, sample_rate, audiostreamer)
    return translate(transcript, 'en', 'fr')
