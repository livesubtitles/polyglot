from server.languagedetectors.microsoft import *

languagedetector = microsoftLanguageDetector()

def detect_language(audio_file):
    return languagedetector.detect_language(audio_file)
