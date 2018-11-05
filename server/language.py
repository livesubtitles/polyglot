import os
import time
import requests
import urllib
import json
import random

microsoftKey = os.environ.get('MICROSOFTKEY')
microsoftId = os.environ.get('MICROSOFTID')

_LIMIT = 10
_DEFAULT = "en-US"

def _get_access_token(headers):
	url = 'https://api.videoindexer.ai/auth/trial/Accounts/' + microsoftId + '/AccessToken?allowEdit=true'
	response = requests.get(url, headers=headers)
	return response.text.split("\"")[1]

def _get_id_url(access_token):
	url = 'https://api.videoindexer.ai/trial/Accounts/' + microsoftId
	url = url + '/Videos?accessToken=' + access_token
	url = url + '&name=test' + str(random.randint(1, 100))

	return url

def _get_video_id(audio_file, headers, access_token):
	url = _get_id_url(access_token)

	form_data = {'file': audio_file.getvalue()}
	params = urllib.parse.urlencode({'language': 'auto'})

	r = requests.post(url, params=params, files=form_data, headers=headers)
	return (r.json())['id']

def _detection_request(video_id, headers, access_token):
	url = 'https://api.videoindexer.ai/trial/Accounts/' + microsoftId 
	url = url + '/Videos/' + video_id
	url = url + '/Index?accessToken=' + access_token

	r = requests.get(url, headers=headers)
	return (r.json())['videos'][0]['insights']['sourceLanguage']


########### PUBLIC FUNCTIONS ###########

def detect_language(audio_file):
	headers = {'Ocp-Apim-Subscription-Key': microsoftKey}
	access_token = _get_access_token(headers)
	
	try:
		video_id = _get_video_id(audio_file, headers, access_token)
	except Exception as e:
		print("Error with finding video ID from Microsoft API")
		print(str(e))
		return "en-US"

	source_lang = None
	try_no = 0

	while(source_lang == None or source_lang == _DEFAULT): 
		if (try_no > _LIMIT):
			print("Detection limit reached. Defaulting to " + _DEFAULT)
			return _DEFAULT

		time.sleep(2)

		print("Detecting language: ", end='')
		source_lang = _detection_request(video_id, headers, access_token)
		
		print (source_lang, end='')
		if source_lang == None:
			print("Retrying...")

		try_no = try_no + 1

	return source_lang
