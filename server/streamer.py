from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from six.moves import queue

class AudioStreamer(object):
    def __init__( self, streaming_config, rate ):
        self.rate = rate
        self.buff = queue.Queue()
        self.closed = True
        # takes in a client such as the google speech client
        self.client = speech.SpeechClient()
        self.streaming_config = streaming_config

    def __enter__( self ):
        self.closed = False

    def __exit__( self, type, value, traceback ):
        self.closed = True
        # Signal generator to terminate
        self.buff.put( None )

    def received_audio_buffer( audio_buffer ):
        self.buff.put( audio_buffer )

    def change_language_code( self, new_language_code ):
        config = types.RecognitionConfig(
                            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
                            sample_rate_hertz=self.rate,
                            language_code=new_language_code
                        )
        self._set_streaming_config( config )


    def _set_streaming_config( self, config, interim_results=False ):
        self.streaming_config = types.StreamingRecognitionConfig(
                                         config=config,
                                         interim_results=interim_results
                                      )

    # Starts the streaming from the audio received to the google speech API
    # takes a callback that will be called with the results from the transcription
    def start( self, callback ):



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
