import unittest
import responses
import os
import server.speechtotext

# apiKey = os.environ.get('APIKEY')
# url = "https://speech.googleapis.com/v1/speech:recognize?key=" + apiKey
#
# class TestSpeechToText(unittest.TestCase):
#
#     @responses.activate
#     def test_speechToText(self):
#         speech = server.speechtotext._convert_to_wav([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000)
#         sourceLang = "fr"
#         mock_response = {
#             "results": [{
#                 "alternatives": [{"transcript": "French chips are good"}]
#             }]
#         }
#         responses.add(responses.POST, url,
#                   json=mock_response, status=200)
#         text = server.speechtotext._speech_to_text(speech, 2000, sourceLang)
#         self.assertEqual( text, "French chips are good" )
#         self.assertEqual( len( responses.calls ), 1 )
#
#     @responses.activate
#     def test_speechToText_exception(self):
#         speech = server.speechtotext._convert_to_wav([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000)
#         sourceLang = "fr"
#         mock_response = {
#             "results": [{
#                 "Some incorrect key": "Some incorrect response"
#             }]
#         }
#         responses.add(responses.POST, url,
#                   json=mock_response, status=200)
#         text = server.speechtotext._speech_to_text(speech, 2000, sourceLang)
#         self.assertEqual( text, "" )
#         self.assertEqual( len( responses.calls ), 1 )
#
# if __name__ == '__main__':
#     unittest.main()
