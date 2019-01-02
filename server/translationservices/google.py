import httplib2
import json
import requests
import urllib
import os

from urllib import parse
from zope.interface import Interface, implementer
from server.adapter import *

# Set endpoints
detection = 'detect'
languages = 'languages'

apiKey = os.environ.get('APIKEY')
url = 'https://www.googleapis.com/language/translate/v2/'

@implementer(TranslationService)
class googleTranslationService(object):

    def __init__(self):
        pass

    def detectAndTranslate(self, textToTranslate, targetLang):
    	sourceLang = self.detect(textToTranslate)['language']
    	return self.translate_no_credentials(textToTranslate, targetLang, sourceLang)

    def translate_no_credentials(self, textToTranslate, targetLang, sourceLang):
    	if (sourceLang == 'detected'):
    		return ""
    	payload = {'key' : apiKey, 'q' : textToTranslate, 'target' : targetLang, 'source' : sourceLang}
    	r = requests.get(url, params = payload)
    	data = r.json()
    	try:
    		res = data['data']['translations'][0]['translatedText']
    		print("Translation: {}".format( res ))
    	except KeyError as exc:
    		print("No Translation Found!")
    		res = ""
    		return res
    	return res

    def translate_with_credentials(self, textToTranslate, targetLang, sourceLang, credentials):
    	if (sourceLang == 'detected'):
    		return ""
    	payload = {'q' : textToTranslate, 'target' : targetLang, 'source' : sourceLang}
    	http = httplib2.Http()
    	http_auth = credentials.authorize(http)
    	print(url + '?q='+ textToTranslate + '&target=en&source='+sourceLang)
    	resp, content = http.request(
    		url + '?q='+ urllib.parse.quote_plus(textToTranslate) + '&target=en&source='+sourceLang)
    	print(resp.status)
    	print(content.decode('utf-8'))
    	json_response = json.loads(content.decode('utf-8'))
    	return json_response['data']['translations'][0]['translatedText']

    def getLanguages(self):
    	payload = {'key' : apiKey}
    	r = requests.get((url + languages), params = payload)
    	data = r.json()
    	print (data['data']['languages'])
    	return (data['data']['languages'])

    def detect(self, textToTranslate):
    	payload = {'key' : apiKey, 'q' : textToTranslate}
    	r = requests.get((url + detection), params = payload)
    	data = r.json()
    	print (data['data']['detections'][0][0])
    	return (data['data']['detections'][0][0])
