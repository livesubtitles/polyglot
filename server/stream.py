import io
import os
import shutil
import subprocess
import streamlink
import wave
import sys
import time
from ffmpy import FFmpeg
from six.moves import queue
from threading import Thread
from enum import Enum

BYTES_TO_READ = 500000
WAIT_TIME	  = 10.0

STD_VIDEO_KEY   = '480p'
INPUT_FILE 		= "streams/temp"
EXTENSION 		= ".ts"
OUTPUT_WAV_FILE = "temp/audio.wav"



# Nukes the temp directory and generates a fresh one
def _clearTempFiles():
	if os.path.isdir('temp'):
		shutil.rmtree('temp')
	os.makedirs('temp')

class _StreamWorker(Thread):
	def __init__(self, buff, stream_data):
		self.buff = buff
		self.stream_data = stream_data
		self.streaming = True
		self.count = 0
		Thread.__init__(self)

	def run(self):
		while self.streaming:
			time.sleep(WAIT_TIME)

			data = self.stream_data.read(BYTES_TO_READ)

			video_file = INPUT_FILE + str(self.count) + EXTENSION

			with open(video_file, "wb") as f:
				f.write(data)

			print("Created file: " + video_file)
			self.count += 1

		self.stream_data.close()

	def stop_queue_worker(self):
		self.streaming = False


class VideoStreamer(object):
	def __init__(self, stream_url):
		self.stream_url = stream_url
		self.buffer = queue.Queue()
		self.sample_rate = None
		self.worker = None

	def get_data(self, num_segments=5):
		video_data = self.buffer.get()

		for i in range(1, num_segments):
			video_data += self.buffer.get()

		video_file = INPUT_FILE + str(self.count) + EXT
		self.count += 1

		with open(video_file, "ab") as f:
			f.write(video_data)

		try:
			audio_data = self._extract_audio(video_file)
		except Exception as e:
			raise Exception("FFMpeg Error")

		self._set_sample_rate()

		return (bytearray(video_data), io.BytesIO(audio_data))

	def get_sample_rate(self):
		return self.sample_rate

	def _extract_audio(self, file_name):
		ff = FFmpeg(
			inputs={file_name:['-hide_banner', '-loglevel', 'panic', '-y']},
			outputs={OUTPUT_WAV_FILE:['-ac', '1', '-vn', '-f', 'wav']}
		)

		ff.run()

		with open(OUTPUT_WAV_FILE, "rb") as f:
			content = f.read()

		return content

	def _set_sample_rate(self):
		if not self.sample_rate:
			wav = wave.open(OUTPUT_WAV_FILE, "rb")
			self.sample_rate = wav.getframerate()
			wav.close()

	def _get_video_stream(self):
		try:
			available_streams = streamlink.streams(self.stream_url)
		except Exception:
			# HANDLE SPECIFIC NOPLUGINERROR OR PLUGINERROR
			raise Exception("Streamlink Unavailable")

		if STD_VIDEO_KEY not in available_streams:
			# HANDLE THE CASE WHERE 480 IS NOT AVAILABLE
			print("Could not find 480p stream")
			raise Exception("Streamlink Unavailable")

		return available_streams[STD_VIDEO_KEY]

	def start(self):
		print("Starting Video Streamer...")
		print("Clearing Temporary Files...", end="")
		_clearTempFiles()
		print("Success!")

		print("Getting Video Stream...", end="")
		stream = self._get_video_stream()

		if stream == None:
			raise Exception("Streamlink Unavailable")
		print("Success!")

		data = stream.open()

		print("Starting stream worker...", end="")
		self.worker = _StreamWorker(self.buffer, data)
		self.worker.start()
		print("Success!")

	def stop(self):
		self.worker.stop()
