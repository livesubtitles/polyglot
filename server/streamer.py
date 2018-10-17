from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from six.moves import queue
from google.oauth2 import service_account

class AudioStreamer(object):
    def __init__( self ):
        self.buff = queue.Queue()
        self.closed = True
        self.is_rate_set = False
        # takes in a client such as the google speech client
        credentials = service_account.Credentials.from_service_account_file("speech-api.json")
        self.client = speech.SpeechClient(credentials=credentials)

    def __enter__( self ):
        self.closed = False
        return self

    def __exit__( self, type, value, traceback ):
        self.closed = True
        # Signal generator to terminate
        self.buff.put( None )

    def received_audio_buffer( self, audio_buffer, sample_rate, language_code ):
        # if no rate had been set, we need to create and set the configuration
        if not self.is_rate_set:
            self.set_rate = True
            self.set_config( language_code, sample_rate )
        self.buff.put( audio_buffer )

    def set_config( self, new_language_code, rate):
        config = types.RecognitionConfig(
                            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
                            sample_rate_hertz=rate,
                            language_code=new_language_code
                        )
        self.streaming_config = types.StreamingRecognitionConfig(
                                         config=config,
                                         interim_results=False
                                      )

    def generator( self ):
        while not self.closed:
            # blocking call until we get the first chunk
            chunk = self.buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self.buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield data
