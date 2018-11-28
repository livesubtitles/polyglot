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
from server.playlist import *
from server.stream import *

QUALITY_INFO = {'worst': (500000, 8),
				'144p': (500000, 8),
				'360p': (1000000, 10),
				'480p': (2000000, 12),
				'720p': (3000000, 15),
				'best': (3000000, 15)}

SUB_SEG_SIZE  = 10

VID_INPUT_FILE	= "segment"
SUB_INPUT_FILE  = "subtitle"
VID_EXTENSION 	= ".ts"
SUB_EXTENSION	= ".vtt"
OUTPUT_WAV_FILE = "/audio.wav"

class _StreamWorker(Thread):
	def __init__(self, stream_data, bytes_to_read, wait_time, language, user, playlist, credentials):
		self.stream_data = stream_data
		self.user_dir = 'streams/' + user
		self.streaming = True
		self.count = 0
		self.current_time = 0
		self.sample_rate = 0
		self.bytes_to_read = bytes_to_read
		self.wait_time = wait_time
		self.credentials = credentials
		self.playlist = playlist
		self.language = language
		Thread.__init__(self)

	def _get_duration(self, video_file):
		output = subprocess.check_output(["ffmpeg -i " + video_file + " 2>&1 | grep 'Duration'"], shell=True)
		duration = output.decode('ascii').split("Duration: ")[1].split(',')[0]
		return float(duration.split(":")[2])

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

	def _get_subtitle(self, audio, sample_rate, raw_pcm=False):
		if self.language == '':
			self.language = detect_language(audio)

		transcript = get_text_from_pcm(audio, sample_rate, self.language) if raw_pcm else \
					 get_text(audio, sample_rate, self.language, self.credentials)
		translated = translate(transcript, 'en', self.language.split('-')[0], self.credentials)
		punctuated = self._get_punctuated(translated)
		print(punctuated)
		punctuated = punctuated.replace(",,", ",").replace("..", ".")
		return punctuated

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
		url = "http://flask-env.p5puf6mmb3.eu-west-2.elasticbeanstalk.com/punctuate"
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
		subtitles = self._get_subtitle(audio_data, self.sample_rate)
		#subtitles = self._get_punctuated(subtitles)

		vtt = WebVTT()

		if subtitles == None or len(subtitles) == 0:
			with open(file_path, 'w') as f:
				vtt.write(f)
			return file_path

		subtitles = subtitles.split()

		max_segment_duration = duration / ceil(len(subtitles) / SUB_SEG_SIZE)
		words_per_segment = ceil(len(subtitles) / (duration / max_segment_duration))

		rem_duration = duration
		word_index = 0

		while rem_duration > 0:
			segment_duration = min(rem_duration, max_segment_duration)
			words_in_segment = subtitles[word_index : word_index + words_per_segment]

			start_time = self._get_current_timestamp()
			self.current_time += segment_duration
			end_time = self._get_current_timestamp()

			vtt.captions.append(Caption(start_time, end_time, " ".join(words_in_segment)))

			word_index += words_per_segment
			rem_duration -= segment_duration

		with open(file_path, 'w') as f:
			vtt.write(f)

		print("Created file: " + file_path)
		return file_path

	def run(self):
		while self.streaming:
			time.sleep(self.wait_time)

			data = self.stream_data.read(self.bytes_to_read)

			video_path = self._create_video_file(data)

			audio_data = self._extract_audio(video_path)
			duration = self._get_duration(video_path)

			audio_path = self._create_subtitle_file(data, audio_data, duration)

			self.playlist.update_all(self.count, duration)
			self.count += 1

		self.stream_data.close()

	def stop(self):
		self.streaming = False


class VideoStreamer(object):
	def __init__(self, stream_url, language, user, credentials):
		self.stream_url = stream_url
		self.language = language
		self.user = user
		self.credentials = credentials
		self.quality = '360p'
		self.worker = None
		self.available_streams = None

	def _get_video_stream(self):
		try:
			self.available_streams = streamlink.streams(self.stream_url)
		except Exception:
			raise Exception("Streamlink Unavailable")

		if self.quality not in self.available_streams:
			print("Could not find " + self.quality + " stream")
			raise Exception("Streamlink Unavailable")

		return self.available_streams[self.quality]

	def get_supported_qualities(self):
		return list(self.available_streams.keys())

	def update_quality(self, new_quality):
		if new_quality == self.quality:
			return

		print("!Stream Quality Update!")

		print("Stopping worker...", end="")
		self.stop()
		print("Success!")

		return self.start(new_quality)

	def start(self, quality='360p'):
		print("Starting Video Streamer with quality: " + quality)
		self.quality = quality

		print("Getting Video Stream...", end="")
		stream = self._get_video_stream()
		print("Success!")

		print("Opening stream...", end="")
		data = stream.open()
		print("Success!")

		print("Creating playlist...", end="")
		playlist = HLSPlaylist(self.user)
		print("Success!")

		(bytes_to_read, wait_time) = QUALITY_INFO[self.quality]

		print("Starting stream worker...", end="")
		self.worker = _StreamWorker(data, bytes_to_read, wait_time, self.language,
			self.user, playlist, self.credentials)
		self.worker.start()
		print("Success!")

		return playlist

	def stop(self):
		if self.worker != None:
			self.worker.stop()
			self.worker.join()
			self.worker = None
