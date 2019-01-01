from zope.interface import Interface, implementer

class LanguageDetectionService(Interface):
    def detect_language(audio_file):
        pass

class TranscriptionService(Interface):
    def _speech_to_text(audiobase64, sample_rate, lang, credentials):
        pass

class TranslationService(Interface):
    def detectAndTranslate(textToTranslate, targetLang):
        pass

    def translate_no_credentials(textToTranslate, targetLang, sourceLang):
        pass

    def translate_with_credentials(textToTranslate, targetLang, sourceLang, credentials):
        pass

class PunctuatorService(Interface):
    def punctuate(input_text):
        pass
