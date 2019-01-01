import os
import time
import requests
import urllib
import json
import random
import uuid
from zope.interface import Interface, implementer
from server.adapter import *

microsoftKey = os.environ.get('MICROSOFTKEY')
microsoftId = os.environ.get('MICROSOFTID')

_LIMIT = 20
_DEFAULT = "en-US"

def _get_random_filename():
    return str(uuid.uuid4())

def _get_id_url(access_token):
    url = 'https://api.videoindexer.ai/trial/Accounts/' + microsoftId
    url = url + '/Videos?accessToken=' + access_token
    url = url + '&name=test'
    params = urllib.parse.urlencode({'language': 'auto'})
    url = url + '&' + params

    return url

def _get_video_id(audio_file, headers, access_token):
    url = _get_id_url(access_token)

    form_data = {'file': audio_file.getvalue()}

    r = requests.post(url, files=form_data, headers=headers)
    return (r.json())['id']

def _detection_request(video_id, headers, access_token):
    url = 'https://api.videoindexer.ai/trial/Accounts/' + microsoftId
    url = url + '/Videos/' + video_id
    url = url + '/Index?accessToken=' + access_token

    r = requests.get(url, headers=headers)
    return (r.json())['videos'][0]['insights']['sourceLanguage']

@implementer(LanguageDetectionService)
class microsoftLanguageDetector(object):

    def __init__(self):
        pass

    def _get_access_token(self, headers):
        url = 'https://api.videoindexer.ai/auth/trial/Accounts/' + microsoftId + '/AccessToken?allowEdit=true'
        response = requests.get(url, headers=headers)
        return response.text.split("\"")[1]

    def detect_language(self, audio_file):
        print("Detecting Language...")
        headers = {'Ocp-Apim-Subscription-Key': microsoftKey}
        access_token = self._get_access_token(headers)

        try:
            video_id = _get_video_id(audio_file, headers, access_token)
        except Exception as e:
            print("Error with finding video ID from Microsoft API")
            print(str(e))
            return "en-US"

        source_lang = None
        try_no = 0

        try:
            while(source_lang == None or source_lang == _DEFAULT):
                if (try_no > _LIMIT):
                    print("\tDetection limit reached. Defaulting to " + _DEFAULT)
                    return _DEFAULT

                time.sleep(2)

                print("\tFound: ", end='')
                source_lang = _detection_request(video_id, headers, access_token)

                print (source_lang, end='')
                if source_lang == None:
                    print(" (Retrying)")

                try_no = try_no + 1
        except Exception as e:
            print("Error with retrieving source language of the video")
            print(str(e))
            return "en-US"


        print("\n\n\n")
        return source_lang
