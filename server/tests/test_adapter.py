import unittest
import mock
from mock import *

import server.translate
from server.translationservices.google import *

import server.speechtotext
from server.transcriptionservices.google import *

import server.language
from server.languagedetectors.microsoft import *

import server.punctuator2.punctuator
from server.punctuator2.theanopunctuator import *

class TranslationAdapterTest(unittest.TestCase):

    def test_translation(self):
        textToTranslate = "Je m'appelle Pablo, et j'aime le fromage."
        targetLang = "en"
        sourceLang = "fr"
        with patch.object(server.translationservices.google.googleTranslationService,
        'translate_no_credentials', return_value='Whatever') as mock_method:
            result = server.translate.translate(textToTranslate, targetLang, sourceLang, None)
            self.assertEqual(result, "Whatever")
            mock_method.assert_called_once_with("Je m'appelle Pablo, et j'aime le fromage.",
            "en", "fr")

class TranscriptionAdapterTest(unittest.TestCase):

    def test_transcription(self):
        pcm_data = [-0.9, 0.45, 0, 0.42, -0.32, 0]
        sample_rate = 2000
        speech = server.speechtotext._convert_to_wav(pcm_data, sample_rate)
        audiobase64 = server.speechtotext._convert_to_base64(speech)
        sourceLang = "fr"
        with patch.object(server.transcriptionservices.google.googleTranscriptionService,
        '_speech_to_text', return_value='French chips are good') as mock_method:
            result = server.speechtotext.get_text_from_pcm(pcm_data, sample_rate, sourceLang, None)
            self.assertEqual(result, "French chips are good")
            mock_method.assert_called_once_with(audiobase64, sample_rate, sourceLang, None)

class PunctuatorAdapterTest(unittest.TestCase):

    def test_punctuator(self):
        model_file = None
        input_text = "my name is hang li li i am studying computer science"
        with patch.object(server.punctuator2.theanopunctuator.theanoPunctuator,
        'punctuate', return_value='My name is Hang Li Li. I am studying Computer Science.') as mock_method:
            result = server.punctuator2.punctuator.punctuate(input_text, model_file)
            self.assertEqual(result, "My name is Hang Li Li. I am studying Computer Science.")
            mock_method.assert_called_once_with(input_text)

class LanguageAdapterTest(unittest.TestCase):

    def test_language_detection(self):
        speech = server.speechtotext._convert_to_wav([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000)
        with patch.object(server.languagedetectors.microsoft.microsoftLanguageDetector,
        'detect_language', return_value='FR-fr') as mock_method:
            result = server.language.detect_language(speech)
            self.assertEqual(result, "FR-fr")
            mock_method.assert_called_once_with(speech)
