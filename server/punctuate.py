import io
import requests

HOST = 'http://bark.phon.ioc.ee/punctuator'
LOWEST_STATUS_CODE = 200
HIGHEST_STATUS_CODE = 399
def punctuate(text):
     r = requests.post(HOST, data = {'text':"hello world"})
     if r.status_code >= 200 and r.status_code <= 399:
          return r.text
     return text
