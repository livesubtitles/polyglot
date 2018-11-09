# class StreamingSocket(Namespace):

#     streamer = None
#     language = None

#     def _initialise_streamer(self, url):
#         self.streamer = VideoStreamer(url)

#         try:
#             self.streamer.start()
#         except Exception:
#             emit('stream-response', jsonify(video="", subtitle="", error="Streamlink Unavailable!"))

#     def on_connect(self):
#         print("Connected to client")

#     def on_disconnect(self):
#         self.streamer.stop()
#         print("Disconnected from client")

#     def on_stream(self, data):
#         if self.streamer == None:
#             self._initialise_streamer(data['url'])

#         lang = data['lang']
        
#         if lang == '':
#             (video, audio) = self.streamer.get_data()
#             lang = detect_language(audio)

#         self.language = lang

#         print("Successfully initialised streamer. Ready to stream!")

#         emit('stream-response', json.dumps({'video':'', 'subtitles':''}))

#     def on_ready(self):
#         print("Ready to send data to client...")
#         (video, audio) = self.streamer.get_data()
#         sample_rate    = self.streamer.get_sample_rate()

#         transcript = get_text(audio, sample_rate, self.language)
#         translated = translate(transcript, 'en', self.language.split('-')[0])

#         response = json.dumps({'video':jsonpickle.encode(video), 'subtitles':translated})
        
#         print("Sending response: " + response)
#         emit('stream-response', response)

# socketio.on_namespace(StreamingSocket('/stream'))