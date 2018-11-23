import httplib2
import json
import requests
import urllib
import os

from urllib import parse

# Set endpoints
detection = 'detect'
languages = 'languages'
url = 'https://www.googleapis.com/language/translate/v2/'

def detectAndTranslate(textToTranslate, targetLang):
	sourceLang = detect (textToTranslate)['language']
	return translate(textToTranslate, targetLang, sourceLang)

def translate(textToTranslate, targetLang, sourceLang, credentials):
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

def getLanguages():
	r = requests.get((url + languages), params = payload)
	data = r.json()
	print (data['data']['languages'])
	return (data['data']['languages'])

def detect(textToTranslate):
	payload = {'q' : textToTranslate}
	r = requests.get((url + detection), params = payload)
	data = r.json()
	print (data['data']['detections'][0][0])
	return (data['data']['detections'][0][0])


def test():
	return detectAndTranslate("Estoy bebiendo agua.", "en")
