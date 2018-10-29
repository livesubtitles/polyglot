import requests
import os

# Set endpoints
translation = ''
detection = 'detect'
languages = 'languages'

apiKey = os.environ.get('APIKEY')
url = 'https://www.googleapis.com/language/translate/v2/'

def detectAndTranslate(textToTranslate, targetLang):
    sourceLang = detect (textToTranslate)['language']
    return translate(textToTranslate, targetLang, sourceLang)

def translate(textToTranslate, targetLang, sourceLang):
    if (sourceLang == 'detected'):
        return ""
    payload = {'key' : apiKey, 'q' : textToTranslate, 'target' : targetLang, 'source' : sourceLang}
    r = requests.get((url + translation), params = payload)
    data = r.json()
    try:
        res = data['data']['translations'][0]['translatedText']
        print(res)
    except KeyError as exc:
        print(exc)
        res = ""
    return res


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
