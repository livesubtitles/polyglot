import unittest
import responses
import os
import server.speechtotext
from server.transcriptionservices.google import *
import mock
from mock import *

apiKey = os.environ.get('APIKEY')
url = "https://rumosrucml.execute-api.us-east-2.amazonaws.com/api/transcribe"

googletranscriptionservice = googleTranscriptionService()

class TestSpeechToText(unittest.TestCase):

            # url = "https://rumosrucml.execute-api.us-east-2.amazonaws.com/api/transcribe"
            # audiores = {}
            # audiores['content'] = audiobase64
            # body = {}
            # body['audio'] = audiores
            # body['sample_rate'] = sample_rate
            # body['lang'] = lang
            # print(body)
            # data = json.dumps(body)
            # print(data)
            # headers = {'content-type': 'application/json'}
            # resp = requests.post(url, data=data, headers = headers)
            # print(resp.text)
            # translated = resp.text

    @responses.activate
    def test_speechToText(self):
        speech = server.speechtotext._convert_to_wav([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000)
        audiobase64 = server.speechtotext._convert_to_base64(speech)
        sourceLang = "fr"
        mock_response = 'French chips are good'
        responses.add(responses.POST, url, body=mock_response, status=200)
        text = googletranscriptionservice._speech_to_text(audiobase64, 2000, sourceLang, None, "en")
        self.assertEqual(text, "French chips are good")
        self.assertEqual(len(responses.calls), 1)

if __name__ == '__main__':
    unittest.main()
