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

'''
	New Workflow:

	- On socket connection, create a hash for the user
	- Streamer starts. It creates a new directory for the user.
	- It creates a playlist file in this directory and sets off a stream worker.
	- Every 10 seconds, the stream worker reads from the stream and writes to a temp file.
	- The stream worker adds the name of the temp file into the current playlist file.
	- The streamer should return the name of the playlist file to be used by hls.

'''

BYTES_TO_READ = 1000000
WAIT_TIME	  = 10.0

STD_VIDEO_KEY   = '480p'
INPUT_FILE		= "segment"
EXTENSION 		= ".ts"
OUTPUT_WAV_FILE = "temp/audio.wav"

# Nukes the temp directory and generates a fresh one
def _clearTempFiles():
	if os.path.isdir('temp'):
		shutil.rmtree('temp')
	os.makedirs('temp')

class _StreamWorker(Thread):
	def __init__(self, buff, stream_data, user_dir):
		self.buff = buff
		self.stream_data = stream_data
		self.user_dir = user_dir
		self.streaming = True
		self.count = 0
		Thread.__init__(self)

	def _update_playlist(self, video_file):
		playlist_path = self.user_dir + '/playlist.m3u8'

		if not os.path.isfile(playlist_path):
			print("Playlist not found, exiting...")
			raise Exception

		with open(playlist_path, "r") as f:
			lines = f.readlines()

		sequence_no = int(lines[3].split(':')[1])

		lines[3] = '#EXT-X-MEDIA-SEQUENCE:' + str(sequence_no + 1) + '\n'

		with open(playlist_path, "w+") as f:
			f.writelines(lines)
			f.write('#EXTINF:8.0000,\n')
			f.write(video_file + '\n')

	def run(self):
		while self.streaming:
			time.sleep(WAIT_TIME)

			data = self.stream_data.read(BYTES_TO_READ)

			video_file = INPUT_FILE + str(self.count) + EXTENSION
			path = self.user_dir + '/'

			print("Writing file with path: " + path + video_file)

			with open(path + video_file, "wb") as f:
				f.write(data)

			print("Created file: " + video_file)

			try:
				self._update_playlist(video_file)
			except Exception as exe:
				print(exe)
				return

			self.count += 1

		self.stream_data.close()

	def stop(self):
		self.streaming = False


class VideoStreamer(object):
	def __init__(self, stream_url, user_dir):
		self.stream_url = stream_url
		self.user_dir = user_dir
		self.buffer = queue.Queue()
		self.sample_rate = None
		self.worker = None

	# def get_data(self, num_segments=5):
	# 	video_data = self.buffer.get()

	# 	for i in range(1, num_segments):
	# 		video_data += self.buffer.get()

	# 	video_file = INPUT_FILE + str(self.count) + EXT
	# 	self.count += 1

	# 	with open(video_file, "ab") as f:
	# 		f.write(video_data)

	# 	try:
	# 		audio_data = self._extract_audio(video_file)
	# 	except Exception as e:
	# 		raise Exception("FFMpeg Error")

	# 	self._set_sample_rate()

	# 	return (bytearray(video_data), io.BytesIO(audio_data))

	# def get_sample_rate(self):
	# 	return self.sample_rate

	# def _extract_audio(self, file_name):
	# 	ff = FFmpeg(
	# 		inputs={file_name:['-hide_banner', '-loglevel', 'panic', '-y']},
	# 		outputs={OUTPUT_WAV_FILE:['-ac', '1', '-vn', '-f', 'wav']}
	# 	)

	# 	ff.run()

	# 	with open(OUTPUT_WAV_FILE, "rb") as f:
	# 		content = f.read()

	# 	return content

	# def _set_sample_rate(self):
	# 	if not self.sample_rate:
	# 		wav = wave.open(OUTPUT_WAV_FILE, "rb")
	# 		self.sample_rate = wav.getframerate()
	# 		wav.close()

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

		print("Getting Video Stream...", end="")
		stream = self._get_video_stream()

		if stream == None:
			raise Exception("Streamlink Unavailable")
		print("Success!")

		print("Opening stream...", end="")
		data = stream.open()
		print("Success!")

		print("Starting stream worker...", end="")
		self.worker = _StreamWorker(self.buffer, data, self.user_dir)
		self.worker.start()
		print("Success!")

	def stop(self):
		self.worker.stop()
