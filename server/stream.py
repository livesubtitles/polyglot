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
from enum import Enum

BYTES_TO_READ = 100000
AUDIO_STREAM_KEY = 'audio_only'
VIDEO_STREAM_KEY = 'worst'
TEMP_INPUT_FILE = "temp.ts"
OUTPUT_WAV_FILE = "audio.wav"

class StreamDataType(Enum):
	AUDIO = 0
	VIDEO = 1

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
				self.buff.put( data )

		self.stream_data.close()

	def stop_queue_worker(self):
		self.streaming = False

class Streamer(object):

	def __init__(self, stream_url):
		self.stream_url = stream_url
		self.buff = queue.Queue()
		self.worker = None
		self.sample_rate = None
		self.data_type = None
		print("**** INITIALISED STREAMER ***** ")

	def get_sample_rate(self):
		"""
			Returns the sample rate. This is not available until the
			first time get_data is called (we return None).
		"""
		return self.sample_rate

	def get_data(self, num_segments):
		with open(TEMP_INPUT_FILE, "ab") as f:
			for x in range(num_segments):
				data = self.buff.get()
				f.write(data)

		try:
			self._transcode_audio()
		except Exception as e:
			raise Exception("Streamlink Unavailable")

		# self._transcode_audio()

		with open(OUTPUT_WAV_FILE, "rb") as f:
			content = f.read()

		self._set_sample_rate()
		self._clear_files()

		return io.BytesIO(content)

	def _transcode_audio(self):

		out_args = ['-ac', '1']

		if self.data_type == StreamDataType.VIDEO:
			out_args.extend(['-vn','-f','wav'])

		ff = FFmpeg(
			inputs={TEMP_INPUT_FILE:None},
			outputs={OUTPUT_WAV_FILE:out_args}
		)

		ff.run()

	def _set_sample_rate(self):
		if not self.sample_rate:
			wav = wave.open(OUTPUT_WAV_FILE, "rb")
			self.sample_rate = wav.getframerate()
			wav.close()

	@staticmethod
	def _remove_if_present(file):
		print(os.path.isfile(file))
		if os.path.isfile(file):
			os.remove(file)

	def _clear_files(self):
		Streamer._remove_if_present(TEMP_INPUT_FILE)
		Streamer._remove_if_present(OUTPUT_WAV_FILE)

	def _get_audio_stream(self):
		print("***** Getting audio stream ******")
		try:
			available_streams = streamlink.streams(self.stream_url)
		except Exception as exe:
            #Streamlink is unavailable on this website
			return None

		if AUDIO_STREAM_KEY not in available_streams:
			# video stream
			self.data_type = StreamDataType.VIDEO
			res = available_streams[VIDEO_STREAM_KEY]
			print("***** FOUND VIDEO STREAM *****")
		else:
			self.data_type = StreamDataType.AUDIO
			res = available_streams[AUDIO_STREAM_KEY]
			print("****** FOUND AUDIO STREAM ******")
		return res

	def start(self):

		print("**** BEFORE CLEARING FILES ****")

		self._clear_files()

		print("**** AFTER CLEARING FILES ****")

		audio_stream = self._get_audio_stream()

		if audio_stream == None:
			raise Exception("Streamlink Unavailable")

		print("**** OPENING AUDIO STREAM ****")

		print("$$$$$ CURRENT UNIX TIME: " + str(time.time()))

		stream_data = audio_stream.open()

		print("**** CALCULATING BYTES TO READ ****")

		print("**** CREATING STREAM WORKER ****")

		self.worker = _StreamWorker(self.buff, stream_data)
		self.worker.start()

	def stop(self):
		self.worker.stop_queue_worker()
