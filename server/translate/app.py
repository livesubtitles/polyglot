from chalice import Chalice
from botocore.vendored import requests
import os
from chalicelib.speechtotext import *
from chalicelib.translate import *
import json

app = Chalice(app_name='translate')
app.debug = True

# Set endpoints
detection = 'detect'
languages = 'languages'

apiKey = ''
url = 'https://www.googleapis.com/language/translate/v2/'

@app.route('/')
def index():
    return {'Hello' : getText()}

@app.route('/transcribe', methods=['POST'])
def transcribe_text():
    request_body = app.current_request.json_body
    audio = request_body['audio']
    sample_rate = request_body['sample_rate']
    lang = request_body['lang']
    transcript = get_text(audio, sample_rate, lang)
    translated = translate(transcript, 'en', lang.split('-')[0])
    return {"subtitle" : translated}

# @app.route('/translate/{name}')
# def hello_name(name):
#     global apiKey
#     apiKey = os.environ['apiKey']
#     r = detectAndTranslate(name, "en")
#     return r
#
# def detectAndTranslate(textToTranslate, targetLang):
#     sourceLang = detect (textToTranslate)['language']
#     return translate(textToTranslate, targetLang, sourceLang)
#
# def translate(textToTranslate, targetLang, sourceLang):
#     if (sourceLang == 'detected'):
#         return ""
#     payload = {'key' : apiKey, 'q' : textToTranslate, 'target' : targetLang, 'source' : sourceLang}
#     r = requests.get(url, params = payload)
#     data = r.json()
#     try:
#         res = data['data']['translations'][0]['translatedText']
#         print("Translation: {}".format( res ))
#     except KeyError as exc:
#         print("Exception with key: {}".format( exc ))
#         res = ""
#     return res
#
# def getLanguages():
#     payload = {'key' : apiKey}
#     r = requests.get((url + languages), params = payload)
#     data = r.json()
#     print (data['data']['languages'])
#     return (data['data']['languages'])
#
# def detect(textToTranslate):
#     payload = {'key' : apiKey, 'q' : textToTranslate}
#     r = requests.get((url + detection), params = payload)
#     data = r.json()
#     print (data['data']['detections'][0][0])
#     return (data['data']['detections'][0][0])


#
# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:

# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}

# See the README documentation for more examples.
