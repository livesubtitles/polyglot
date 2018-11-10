import unittest
import responses
import os
import server.language
import server.speechtotext
import urllib
import unittest.mock

microsoftKey = os.environ.get('MICROSOFTKEY')
microsoftId = os.environ.get('MICROSOFTID')
headers = {
    'Ocp-Apim-Subscription-Key': microsoftKey
}

urlOfAPIKey = "https://api.videoindexer.ai/auth/trial/Accounts/" + microsoftId + "/AccessToken?allowEdit=true"

class TestDetectLanguage(unittest.TestCase):

    @responses.activate
    def test_getAccessToken(self):
        mock_response = "at123"
        responses.add(responses.GET, urlOfAPIKey, json=mock_response, status=200)
        accessToken = server.language._get_access_token(headers)
        self.assertEqual(accessToken, "at123")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_detectLanguage(self):
        speech = server.speechtotext._convert_to_wav([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000)
        video_id = "123456789"
        mock_response0 = "at123"
        params = urllib.parse.urlencode({
            'language': 'auto',
        })
        urlOfLan = 'https://api.videoindexer.ai/trial/Accounts/' + microsoftId + '/Videos?accessToken=' + mock_response0 + '&name=test' + '&' + params
        urlOfGettingLan = 'https://api.videoindexer.ai/trial/Accounts/' + microsoftId + '/Videos/' + video_id + '/Index?accessToken=' + mock_response0
        mock_response1 = {
            "id": video_id
        }
        mock_response2 = {
            "videos": [{
                "insights": {"sourceLanguage": "FR-fr"}
            }]
        }
        responses.add(responses.POST, urlOfLan, json=mock_response1, status=200)
        responses.add(responses.GET, urlOfAPIKey, json=mock_response0, status=200)
        responses.add(responses.GET, urlOfGettingLan, json=mock_response2, status=200)
        languageDetected = server.language.detect_language(speech)
        self.assertEqual(languageDetected, "FR-fr")
        self.assertEqual(len(responses.calls), 3)


    @responses.activate
    def test_detectLanguage_exception(self):
        speech = server.speechtotext._convert_to_wav([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000)
        video_id = "123456789"
        mock_response0 = "at123"
        params = urllib.parse.urlencode({
            'language': 'auto',
        })
        urlOfLan = 'https://api.videoindexer.ai/trial/Accounts/' + microsoftId + '/Videos?accessToken=' + mock_response0 + '&name=test' + '&' + params
        urlOfGettingLan = 'https://api.videoindexer.ai/trial/Accounts/' + microsoftId + '/Videos/' + video_id + '/Index?accessToken=' + mock_response0
        mock_response1 = {
            "id": video_id
        }
        mock_response2 = {
            "videos": [{
                "insights": {"Some incorrect key": "Some incorrect value"}
            }]
        }
        responses.add(responses.POST, urlOfLan, json=mock_response1, status=200)
        responses.add(responses.GET, urlOfAPIKey, json=mock_response0, status=200)
        responses.add(responses.GET, urlOfGettingLan, json=mock_response2, status=200)
        languageDetected = server.language.detect_language(speech)
        self.assertEqual(languageDetected, "en-US")
        self.assertEqual(len(responses.calls), 3)

if __name__ == '__main__':
    unittest.main()
