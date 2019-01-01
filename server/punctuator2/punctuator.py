from server.punctuator2.theanopunctuator import *

def punctuate(input_text, model_file):
    punctuator = theanoPunctuator(model_file)
    return punctuator.punctuate(input_text)
