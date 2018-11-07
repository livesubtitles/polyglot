from punctuator2.punctuator import *

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
    preprocessed_text = preprocess_text(subtitle)
    model_path = "./punctuator2/Demo-Europarl-EN.pcl"
    return remove_punctuation_annotations(punctuate(preprocessed_text, model_path))

def preprocess_text(subtitle):
    return subtitle.lower()

#print(punctuate_subtitle("Hello do you like cheese I like cheese how about you"))
