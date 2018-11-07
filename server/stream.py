import io
import os
import shutil
import subprocess
import streamlink
import wave
import sys
import time
import contextlib
import server.speechtotext as stt
import server.translate as trn
from ffmpy import FFmpeg
from six.moves import queue
from threading import Thread
from enum import Enum

BYTES_TO_READ = 100000
AUDIO_STREAM_KEY = 'audio_only'
VIDEO_STREAM_KEY = 'worst'
STD_VIDEO_KEY    = '480p'
TEMP_INPUT_FILE  = "temp/temp.ts"
OUTPUT_WAV_FILE  = "temp/audio.wav"

# Nukes the temp directory and generates a fresh one
def _clearTempFiles():
	shutil.rmtree('temp')
	os.makedirs('temp')

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
				self.buff.put(data)

		self.stream_data.close()

	def stop_queue_worker(self):
		self.streaming = False


class VideoStreamer(object):
	def __init__(self, stream_url):
		self.stream_url = stream_url
		self.buffer = queue.Queue()
		self.sample_rate = None
		self.worker = None

	def get_data(self, num_segments=3):

		video_data = self.buffer.get()

		with open(TEMP_INPUT_FILE, "ab") as f:
			f.write(video_data)

		try:
			audio_data = self._extract_audio()
		except Exception as e:
			raise Exception("FFMpeg Error")

		self._set_sample_rate()
		_clearTempFiles()

		return (bytearray(video_data), io.BytesIO(audio_data))

	def get_sample_rate(self):
		return self.sample_rate

	def _extract_audio(self):
		ff = FFmpeg(
			inputs={TEMP_INPUT_FILE:['-hide_banner', '-loglevel', 'panic', '-y']},
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







##################################################################################
################################# AUDIO STREAMER #################################
##################################################################################

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
		self.data_type = None

		print("Initialised Streamer...")

	def get_sample_rate(self):
		"""
			Returns the sample rate. This is not available until the
			first time get_data is called (we return None).
		"""
		return self.sample_rate

	def get_data(self, num_segments=3):
		with open(TEMP_INPUT_FILE, "ab") as f:
			for x in range(num_segments):
				data = self.buff.get()
				f.write(data)

		try:
			self._transcode_audio()
		except Exception as e:
			raise Exception("Streamlink Unavailable")

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
		if os.path.isfile(file):
			os.remove(file)

	def _clear_files(self):
		print("Cleaning up temp files... ", end='')
		Streamer._remove_if_present(TEMP_INPUT_FILE)
		Streamer._remove_if_present(OUTPUT_WAV_FILE)
		print("Success!")

	def _get_audio_stream(self):
		print("Getting stream... ", end='')

		try:
			available_streams = streamlink.streams(self.stream_url)
		except Exception as exe:
            #Streamlink is unavailable on this website
			return None

		if AUDIO_STREAM_KEY not in available_streams:
			# video stream
			self.data_type = StreamDataType.VIDEO
			res = available_streams[VIDEO_STREAM_KEY]
		else:
			self.data_type = StreamDataType.AUDIO
			res = available_streams[AUDIO_STREAM_KEY]

		print("Success!")
		return res

	def start(self):
		self._clear_files()

		audio_stream = self._get_audio_stream()

		if audio_stream == None:
			raise Exception("Streamlink Unavailable")

		stream_data = audio_stream.open()

		print("Starting StreamWorker... ", end='')
		self.worker = _StreamWorker(self.buff, stream_data)
		self.worker.start()
		print("Success!")

	def stop(self):
		self.worker.stop_queue_worker()
