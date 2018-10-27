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

import sys
import re
def listen_print_loop(responses):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0
    for response in responses:
        print("NAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAN")
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0



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
        listen_print_loop(responses)

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
