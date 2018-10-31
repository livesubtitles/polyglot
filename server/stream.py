import io
import os
import subprocess
import streamlink
import wave
import sys
import time
import server.speechtotext as stt
import server.translate as trn
from ffmpy import FFmpeg
from six.moves import queue
from threading import Thread

BYTES_TO_READ = 100000

class _StreamWorker(Thread):
	def __init__(self, buff, stream_data):
		self.buff = buff
		self.stream_data = stream_data
		self.streaming = True
		Thread.__init__(self)

	def run(self):
		while self.streaming:
			data = self.stream_data.read(BYTES_TO_READ)
			if data != '':
				print("Getting data...")
				self.buff.put(data)

		self.stream_data.close()

	def stop_queue_worker(self):
		self.streaming = False

class Streamer(object):

	def __init__(self, stream_url):
		self.stream_url = stream_url
		self.buff = queue.Queue()
		self.worker = None
		self.sample_rate = None

	def get_sample_rate(self):
		"""
			Returns the sample rate. This is not available until the
			first time get_data is called (we return None).
		"""
		return self.sample_rate

	def get_data(self, num_segments):
		print("before open")

		with open("audio.ts", "ab") as f:
			for x in range(num_segments):
				data = self.buff.get()
				f.write(data)
		print("after open")

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

	def _get_audio_stream(self):
		try:
			available_streams = streamlink.streams(self.stream_url)
		except Exception:
			print("e1")
            #Streamlink is unavailable on this website
			return None

		if "audio_only" not in available_streams:
			print("e2")
            #Could not find audio only stream, handle video stream
			return None

		return available_streams['audio_only']

	def start(self):
		audio_stream = self._get_audio_stream()

		if audio_stream == None:
			raise Exception("Streamlink Unavailable")  # TODO: Raise exception

		stream_data = audio_stream.open()

		self.worker = _StreamWorker(self.buff, stream_data)
		self.worker.start()

	def stop(self):
		self.worker.stop_queue_worker()
