import os.path

from punctuator2.punctuator import *

def segment_model():
    f1 = open("./punctuator2/model1.pcl", "wb")
    f2 = open("./punctuator2/model2.pcl", "wb")
    model = open("./punctuator2/Demo-Europarl-EN.pcl", "rb")
    count = 0
    for line in model:
        if (count <= 200000):
            f1.write(line)
        else:
            f2.write(line)
        count = count + 1
    f1.close()
    f2.close()
    model.close()

def prepare_model_file():
    f1 = open("./punctuator2/model1.pcl", "rb")
    final_file = open("./punctuator2/final-model.pcl", "wb")
    for line in f1:
        final_file.write(line)
    f1.close()
    print("Writing first file completed")
    f2 = open("./punctuator2/model2.pcl", "rb")
    for line in f2:
        final_file.write(line)
    f2.close()
    print("Writing second file completed")
    final_file.close()

def remove_punctuation_annotations(subtitle):
    result = ""
    first_caps = True
    for word in subtitle.split(" "):
        if (word == ",COMMA"):
            result = result[:-1]
            result += ", "
        elif (word == "?QUESTIONMARK"):
            result = result[:-1]
            result += "? "
            first_caps = True
        elif (word == ".PERIOD"):
            result = result[:-1]
            result += ". "
            first_caps = True
        elif (word == "!EXCLAMATIONMARK"):
            result = result[:-1]
            result += "! "
            first_caps = True
        elif (word == ":COLON"):
            result = result[:-1]
            result += ": "
        elif (word == ";SEMICOLON"):
            result = result[:-1]
            result += "; "
        elif (word == "-DASH"):
            result = result[:-1]
            result += "-"
        elif (word == "i"):
            result += "I "
            first_caps = False
        else:
            if (first_caps):
                word = ("".join(c.upper() if i == 0 else c for i,c in enumerate(word)))
                first_caps = False
            result += word + " "
    return result[:-2]


def punctuate_subtitle(subtitle):
    if (not os.path.isfile("./punctuator2/final-model.pcl")):
        prepare_model_file()
    preprocessed_text = preprocess_text(subtitle)
    #model_path = "./punctuator2/Demo-Europarl-EN.pcl"
    model_path = "./punctuator2/final-model.pcl"
    return remove_punctuation_annotations(punctuate(preprocessed_text, model_path))

def preprocess_text(subtitle):
    return subtitle.lower()
