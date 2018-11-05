import os
import time
import requests
import urllib
import json
import random

_LIMIT = 10
_DEFAULT = "en-US"

def detect_language(audio_file):
    microsoftKey = os.environ.get('MICROSOFTKEY')
    microsoftId = os.environ.get('MICROSOFTID')
    headers = {
        'Ocp-Apim-Subscription-Key': microsoftKey
    }

    url = 'https://api.videoindexer.ai/auth/trial/Accounts/' + microsoftId + '/AccessToken?allowEdit=true'
    response = requests.get(url, headers=headers)
    access_token = response.text.split("\"")[1]

    form_data = {'file': audio_file.getvalue()}

    params = urllib.parse.urlencode({
        'language': 'auto',
    })

    try:
        url = 'https://api.videoindexer.ai/trial/Accounts/'+ microsoftId + '/Videos?accessToken=' + access_token + '&name=test' + str(random.randint(1, 100))
        r = requests.post(url, params=params, files=form_data, headers=headers)

        video_id = (r.json())['id']
        source_lang = None
        try_no = 0

        while(source_lang == None or source_lang == _DEFAULT):
            try_no = try_no + 1
            
            if (try_no > _LIMIT):
            	print("Detection limit reached. Defaulting to " + _DEFAULT)
            	return _DEFAULT

            time.sleep(2)

            url2 = 'https://api.videoindexer.ai/trial/Accounts/' + microsoftId + '/Videos/' + video_id +'/Index?accessToken=' + access_token
            r = requests.get(url2, headers=headers)
            source_lang = (r.json())['videos'][0]['insights']['sourceLanguage']
            print ("Found source lang: ", source_lang)
        return source_lang
    
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
        return "en-US"
