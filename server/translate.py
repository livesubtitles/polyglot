import httplib2
import json
import requests
import urllib
import os

from urllib import parse
from server.translationservices.google import *

translationService = googleTranslationService()

def detectAndTranslate(textToTranslate, targetLang):
	return translationService.detectAndTranslate(textToTranslate, targetLang)

def translate(textToTranslate, targetLang, sourceLang, credentials):
	if os.environ.get('MODE') != 'paid':
		return translationService.translate_no_credentials(textToTranslate, targetLang, sourceLang)
	return translationService.translate_with_credentials(textToTranslate, targetLang, sourceLang, credentials)

def test():
	return detectAndTranslate("Estoy bebiendo agua.", "en")
