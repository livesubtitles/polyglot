import io
import os
import subprocess
import streamlink
import wave
import server.speechtotext as stt
import server.translate as trn
from ffmpy import FFmpeg
from six.moves import queue
from threading import Thread

class Streamer(object):

	BYTES_TO_READ = 100000

	def __init__(self, stream_url):
		self.stream_url = stream_url
		self.buff = queue.Queue()
		self.streaming = False
		self.sample_rate = None


	def get_sample_rate(self):
		"""
			Returns the sample rate. This is not available until the
			first time get_data is called (we return None).
		"""
		return self.sample_rate

	def get_data(self, num_segments):

		with open("audio.ts", "ab") as f:
			for x in range(num_segments):
				data = self.buff.get()
				f.write(data)

		FFmpeg(
    		inputs={'audio.ts': ['-ac', '1']},
    		outputs={'audio.wav': ['-ac', '1']}
		).run()

		with open("audio.wav", "rb") as f:
			content = f.read()

		if not self.sample_rate:
			wav = wave.open("audio.wav", "rb")
			self.sample_rate = wav.getframerate()
			wav.close()

		os.remove("audio.ts")
		os.remove("audio.wav")

		return io.BytesIO(content)

	def stream(self, stream_data):
		while streaming:
			data = stream_data.read(BYTES_TO_READ)
			if data !== '':
				self.buff.put(data)

		stream_data.close()

	def get_audio(self, available_streams):
		try:
			audio_stream = available_streams['audio_only']
		except KeyError:
			#Handle video using available_streams['worst']
			exit()

	def start(self):
		try:
			available_streams = streamlink.streams(self.stream_url)
		except Exception:
			raise

		audio_stream = self.get_audio(available_streams)

		stream_data = audio_stream.open()

		t = Thread(target=self.stream, args=(stream_data))

		self.streaming = True
		t.start()

	def stop(self):
		self.streaming = False
