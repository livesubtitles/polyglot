import httplib2
import requests
import os

# Set endpoints
detection = 'detect'
languages = 'languages'

apiKey = os.environ.get('APIKEY')
url = 'https://www.googleapis.com/language/translate/v2/'

def detectAndTranslate(textToTranslate, targetLang):
    sourceLang = detect (textToTranslate)['language']
    return translate(textToTranslate, targetLang, sourceLang)

def translate(textToTranslate, targetLang, sourceLang, credentials):
    if (sourceLang == 'detected'):
        return ""
    payload = {'key' : apiKey, 'q' : textToTranslate, 'target' : targetLang, 'source' : sourceLang}
    http = httplib2.Http()
	http_auth = credentials.authorize(http)
    print('https://www.googleapis.com/language/translate/v2/?q='+ targetLang + '&target=en&source='+sourceLang)
	resp, content = http.request(
        'https://www.googleapis.com/language/translate/v2/?q='+ targetLang + '&target=en&source='+sourceLang)
	print(resp.status)
	print(content.decode('utf-8'))
    # r = requests.get(url, params = payload)
    # data = r.json()
    # try:
    #     res = data['data']['translations'][0]['translatedText']
    #     print("Translation: {}".format( res ))
    # except KeyError as exc:
    #     print("Exception with key: {}".format( exc ))
    #     res = ""
    # return res
    return content.decode('utf-8').json()['data']['translations'][0]['translatedText']

def getLanguages():
    payload = {'key' : apiKey}
    r = requests.get((url + languages), params = payload)
    data = r.json()
    print (data['data']['languages'])
    return (data['data']['languages'])

def detect(textToTranslate):
    payload = {'key' : apiKey, 'q' : textToTranslate}
    r = requests.get((url + detection), params = payload)
    data = r.json()
    print (data['data']['detections'][0][0])
    return (data['data']['detections'][0][0])


def test():
    return detectAndTranslate("Estoy bebiendo agua.", "en")
