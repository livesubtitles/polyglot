import unittest
import responses
import os
import server.speechtotext
from server.transcriptionservices.google import *

apiKey = os.environ.get('APIKEY')
url = "https://speech.googleapis.com/v1/speech:recognize?key=" + apiKey

googletranscriptionservice = googleTranscriptionService()

class TestSpeechToText(unittest.TestCase):

    @responses.activate
    def test_speechToText(self):
        speech = server.speechtotext._convert_to_wav([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000)
        audiobase64 = server.speechtotext._convert_to_base64(speech)
        sourceLang = "fr"
        mock_response = {
            "results": [{
                "alternatives": [{"transcript": "French chips are good"}]
            }]
        }
        responses.add(responses.POST, url,
                  json=mock_response, status=200)
        text = googletranscriptionservice._speech_to_text(audiobase64, 2000, sourceLang, None)
        self.assertEqual(text, "French chips are good")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_speechToText_exception(self):
        speech = server.speechtotext._convert_to_wav([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000)
        audiobase64 = server.speechtotext._convert_to_base64(speech)
        sourceLang = "fr"
        mock_response = {
            "results": [{
                "Some incorrect key": "Some incorrect response"
            }]
        }
        responses.add(responses.POST, url,
                  json=mock_response, status=200)
        text = googletranscriptionservice._speech_to_text(audiobase64, 2000, sourceLang, None)
        self.assertEqual(text, "")
        self.assertEqual(len(responses.calls), 1)

if __name__ == '__main__':
    unittest.main()
