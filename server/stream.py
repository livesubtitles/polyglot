import io
import os
import shutil
import subprocess
import streamlink
import wave
import sys
import time
from math import ceil
from datetime import timedelta
from webvtt import WebVTT, Caption
from ffmpy import FFmpeg
from six.moves import queue
from threading import Thread
from enum import Enum

from server.translate import test
from server.speechtotext import *
from server.language import *
from server.stream import *

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
WAIT_TIME	  = 8.0
SUB_SEG_SIZE  = 10

STD_VIDEO_KEY   = '360p'
VID_INPUT_FILE	= "segment"
SUB_INPUT_FILE  = "subtitle"
VID_EXTENSION 	= ".ts"
SUB_EXTENSION	= ".vtt"
OUTPUT_WAV_FILE = "/audio.wav"

SUBTITLE_PLAYLIST = '/subtitles.m3u8'
VIDEO_PLAYLIST    = '/playlist.m3u8'

# Nukes the temp directory and generates a fresh one
def _clearTempFiles():
	if os.path.isdir('temp'):
		shutil.rmtree('temp')
	os.makedirs('temp')

class _StreamWorker(Thread):
	def __init__(self, stream_data, user_dir, video_streamer, credentials):
		self.stream_data = stream_data
		self.user_dir = user_dir
		self.streaming = True
		self.count = 0
		self.current_time = 0
		self.sample_rate = 0
		self.credentials = credentials
		Thread.__init__(self)

	def _update_playlist(self, playlist_name, file_path, duration):
		playlist_path = self.user_dir + playlist_name
		file_name = file_path.split('/')[-1]

		if not os.path.isfile(playlist_path):
			print("Playlist file not found, exiting...")
			raise Exception

		with open(playlist_path, "r") as f:
			lines = f.readlines()

		sequence_no = int(lines[3].split(':')[1])

		lines[3] = '#EXT-X-MEDIA-SEQUENCE:' + str(sequence_no) + '\n'

		if (sequence_no + 1 >= 4 and len(lines) >= 7):
			lines = lines[0:4] + lines[7:]
			lines[3] = '#EXT-X-MEDIA-SEQUENCE:' + str(sequence_no + 1) + '\n'

		with open(playlist_path, "w+") as f:
			f.writelines(lines)
			if not sequence_no == 0:
				f.write('#EXT-X-DISCONTINUITY\n')
			f.write('#EXTINF:' + str(duration) + ',\n')
			f.write(file_name + '\n')

	def _get_duration(self, video_file):
		duration = subprocess.check_output(["ffmpeg -i " + video_file + " 2>&1 | grep 'Duration'"], shell=True)
		duration_time = duration.decode('ascii').split("Duration: ")[1].split(',')[0]
		return float(duration_time.split(":")[2])

	def _extract_audio(self, file_name):
		FFmpeg(
			inputs={file_name:['-hide_banner', '-loglevel', 'panic', '-y']},
			outputs={(self.user_dir + OUTPUT_WAV_FILE):['-ac', '1', '-vn', '-f', 'wav']}
		).run()

		if (self.sample_rate == 0):
			with wave.open(self.user_dir + OUTPUT_WAV_FILE, 'rb') as wav:
				self.sample_rate = wav.getframerate()

		with open(self.user_dir + OUTPUT_WAV_FILE, "rb") as f:
			content = f.read()

		return io.BytesIO(content)

	def _get_next_filepath(self, subtitle):
		return self.user_dir \
			+ '/' \
			+ (SUB_INPUT_FILE if subtitle else VID_INPUT_FILE) \
			+ str(self.count) \
			+ (SUB_EXTENSION if subtitle else VID_EXTENSION)

	def _get_subtitle(self, audio, sample_rate, lang, raw_pcm=False):
		if lang == '':
			lang = detect_language(audio)

		transcript = get_text_from_pcm(audio, sample_rate, lang) if raw_pcm else \
					 get_text(audio, sample_rate, lang, credentials)
		translated = translate(transcript, 'en', lang.split('-')[0], self.credentials)
		return translated

	def _get_current_timestamp(self):
		seconds = self.current_time
		hours, remainder = divmod(seconds, 3600)
		minutes, seconds = divmod(remainder, 60)
		return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)) + '.000'

	def _create_video_file(self, data):
		file_path = self._get_next_filepath(subtitle=False)

		with open(file_path, "wb") as f:
				f.write(data)

		print("Created file: " + file_path)
		self.current_video_file = file_path

		return file_path

	def _get_punctuated(self, subtitle):
		url = "https://polyglot-punctuator.herokuapp.com/punctuate"
		body = {}
		body['subtitle'] = subtitle
		data = json.dumps(body)
		response = requests.post(url, data=data)
		try:
			punctuated = response.json()['subtitle']
		except Exception:
			print("ERROR: Could not punctuate text.")
			return

		return punctuated

	def _create_subtitle_file(self, data, audio_data, duration):
		file_path = self._get_next_filepath(subtitle=True)

		subtitles = self._get_subtitle(audio_data, self.sample_rate, "es-ES")
		# subtitles = self._get_punctuated(subtitles)

		vtt = WebVTT()

		words = subtitles.split()
		num_words = len(words)
		segments = ceil(num_words / SUB_SEG_SIZE)
		window = duration if segments == 0 else ceil(duration / segments)

		for i in range(0, segments - 1):
			start_time = self._get_current_timestamp()
			self.current_time += window
			end_time = self._get_current_timestamp()

			capts = " ".join(words[(i*10):((i*10)+10)])
			vtt.captions.append(Caption(start_time, end_time, capts))

		with open(file_path, 'w') as f:
			vtt.write(f)

		print("Created file: " + file_path)
		return file_path

	def run(self):
		while self.streaming:
			time.sleep(WAIT_TIME)

			data = self.stream_data.read(BYTES_TO_READ)

			video_path = self._create_video_file(data)

			audio_data = self._extract_audio(video_path)
			duration = self._get_duration(video_path)

			audio_path = self._create_subtitle_file(data, audio_data, duration)

			self._update_playlist(VIDEO_PLAYLIST, video_path, duration)
			self._update_playlist(SUBTITLE_PLAYLIST, audio_path, duration)

			self.count += 1

		self.stream_data.close()

	def stop(self):
		self.streaming = False


class VideoStreamer(object):
	def __init__(self, stream_url, user_dir, credentials):
		self.stream_url = stream_url
		self.user_dir = user_dir
		self.credentials = credentials
		self.worker = None

	def _get_video_stream(self):
		try:
			available_streams = streamlink.streams(self.stream_url)
		except NoPluginError:
			raise Exception("Streamlink Unavailable: No Plugin Found")
		except PluginError:
			raise Exception("Streamlink Unavailable: Plugin Error")
		except Exception:
			raise Exception("Streamlink Unavailable")

		if STD_VIDEO_KEY not in available_streams:
			print("Could not find 360p stream")
			raise Exception("Streamlink Unavailable")

		return available_streams[STD_VIDEO_KEY]

	def start(self):
		print("Starting Video Streamer:")

		print("Getting Video Stream...", end="")
		stream = self._get_video_stream()
		print("Success!")

		print("Opening stream...", end="")
		data = stream.open()
		print("Success!")

		print("Starting stream worker...", end="")
		self.worker = _StreamWorker(data, self.user_dir, self, self.credentials)
		self.worker.start()
		print("Success!")

	def stop(self):
		self.worker.stop()
		self.worker.join()
