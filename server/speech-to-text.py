import io
import os
import wave
import struct
import array
# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

# Sends request to Speech-to-Text API
def speech_to_text():
  # Instantiates a client
  client = speech.SpeechClient()

  # The name of the audio file to transcribe
  file_name = 'test.wav'

  # Get audio content
  with io.open(file_name, 'rb') as audio_file:
   content = audio_file.read()
   audio = types.RecognitionAudio(content=content)

  config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=44100,
    language_code='en-US')

  # Detects speech in the audio file
  response = client.recognize(config, audio)

  for result in response.results:
    print('Transcript: {}'.format(result.alternatives[0].transcript))

# Converts audio file to base64 string
def convert_to_base64(wav_file):
  audio_content = wav_file.read()
  return base64.b64encode(audio_content)

# Converts PCM data passed by the front end to a wav file required by the API
def convert_to_wav(pcm_data, sample_rate):
  #temp_file = io.BytesIO()
  file = wave.open('test.wav', 'wb')
  file.setframerate(sample_rate)
  file.setnchannels(1)
  file.setsampwidth(2)
  for i in pcm_data:
      floats = array.array('f', [i])
      samples = [int(sample * 32767)
                  for sample in floats]
      raw_ints = struct.pack("<%dh" % len(samples), *samples)
      file.writeframes(raw_ints)
  file.close()
  #file = wave.open(temp_file, 'rb')


sampleRate = 44100
convert_to_wav(pcm_data, sampleRate)
speech_to_text()