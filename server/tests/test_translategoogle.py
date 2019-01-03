import unittest
import responses
import os
import server.translate
from server.translationservices.google import *

apiKey = os.environ.get('APIKEY')
url = 'https://www.googleapis.com/language/translate/v2/'
url2 = url + 'languages'
url3 = url + 'detect'

translationservice = googleTranslationService()

class TestTranslate(unittest.TestCase):

    @responses.activate
    def test_translate(self):
        textToTranslate = "Je m'appelle Pablo, et j'aime le fromage."
        targetLang = "en"
        sourceLang = "fr"
        mock_response = {
            "data": {
                "translations": [{"translatedText": "Whatever"}]
            }
        }
        responses.add(responses.GET, url,
                  json=mock_response, status=200)
        translation = translationservice.translate_no_credentials(textToTranslate, targetLang, sourceLang)
        self.assertEqual(translation, "Whatever")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_translate_exception(self):
        textToTranslate = "Je m'appelle Pablo, et j'aime le fromage."
        targetLang = "en"
        sourceLang = "fr"
        mock_response = {
            "data": {
                "Some incorrect key": "Some incorrect response"
            }
        }
        responses.add(responses.GET, url,
                  json=mock_response, status=200)
        translation = translationservice.translate_no_credentials(textToTranslate, targetLang, sourceLang)
        self.assertEqual(translation, "")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_getLanguages(self):
        textToTranslate = "Je m'appelle Pablo, et j'aime le fromage."
        targetLang = "en"
        sourceLang = "fr"
        mock_response = {
            "data": {
                "languages": ["es", "en"]
            }
        }
        responses.add(responses.GET, url2, json=mock_response, status=200)
        languages = translationservice.getLanguages()
        self.assertEqual(languages, ["es", "en"])
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_detectAndTranslate(self):
        textToTranslate = "Je m'appelle Pablo, et j'aime le fromage."
        targetLang = "en"
        mock_response1 = {
            "data": {
                "detections": [[{"language": "fr"}]]
            }
        }
        responses.add(responses.GET, url3,
                    json=mock_response1, status=200)
        mock_response2 = {
            "data": {
                "translations": [{"translatedText": "Whatever"}]
            }
        }
        responses.add(responses.GET, url,
                  json=mock_response2, status=200)
        translation = translationservice.detectAndTranslate(textToTranslate, targetLang)
        self.assertEqual(translation, "Whatever")
        self.assertEqual(len(responses.calls), 2)


if __name__ == '__main__':
    unittest.main()
