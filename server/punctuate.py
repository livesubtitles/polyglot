import io
import requests

def punctuate(text):
     r = requests.post('http://bark.phon.ioc.ee/punctuator', data = {'text':"hello world"})
     return r.text
