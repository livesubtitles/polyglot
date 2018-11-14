import io
import os
import shutil
import subprocess
import streamlink
import wave
import sys
import time
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
WAIT_TIME	  = 10.0

STD_VIDEO_KEY   = '360p'
VID_INPUT_FILE	= "segment"
SUB_INPUT_FILE  = "subtitle"
VID_EXTENSION 	= ".ts"
SUB_EXTENSION	= ".vtt"
OUTPUT_WAV_FILE = "temp/audio.wav"

SUBTITLE_PLAYLIST = '/subtitles.m3u8'
VIDEO_PLAYLIST    = '/playlist.m3u8'

# Nukes the temp directory and generates a fresh one
def _clearTempFiles():
	if os.path.isdir('temp'):
		shutil.rmtree('temp')
	os.makedirs('temp')

class _StreamWorker(Thread):
	def __init__(self, buff, stream_data, user_dir, video_streamer):
		self.buff = buff
		self.stream_data = stream_data
		self.user_dir = user_dir
		self.streaming = True
		self.count = 0
		self.start_sending = False
		self.current_time = 0
		self.current_video_file = None
		self.video_streamer = video_streamer
		Thread.__init__(self)

	def _update_playlist(self, playlist_name, file_path):
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
			f.write('#EXTINF:20.0000,\n')
			f.write(file_name + '\n')

	def _get_duration(self, video_file):
		duration = subprocess.check_output(["ffmpeg -i " + video_file + " 2>&1 | grep 'Duration'"], shell=True)
		duration_time = duration.decode('ascii').split("Duration: ")[1].split(',')[0]
		return float(duration_time.split(":")[2])

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
		get_text(audio, sample_rate, lang)
		translated = translate(transcript, 'en', lang.split('-')[0])
		response = {}
		response["subtitle"] = translated
		response["lang"] = lang
		return json.dumps(response)

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
		self._update_playlist(VIDEO_PLAYLIST, file_path)

		return self._get_duration(file_path)

	def _create_subtitle_file(self, data, duration):
		file_path = self._get_next_filepath(subtitle=True)

		video_file = self.current_video_file

		try:
			audio_data = self.video_streamer._extract_audio(video_file)
		except Exception as e:
			raise Exception("FFMPEG error")

		self.video_streamer._set_sample_rate()

		translated_text = self._get_subtitle(io.BytesIO(audio_data), self.video_streamer.get_sample_rate(), "es-ES", False)

		subtitle_and_lang = json.loads(translated_text)
		subtitle = subtitle_and_lang['subtitle']

		print(subtitle)

		start_time = self._get_current_timestamp()
		self.current_time += duration
		end_time = self._get_current_timestamp()

		vtt = WebVTT()
		caption = Caption(start_time,end_time,subtitle)
		vtt.captions.append(caption)

		with open(file_path, 'w') as f:
			vtt.write(f)

		print("Created file: " + file_path)
		self._update_playlist(SUBTITLE_PLAYLIST, file_path)

	def run(self):
		while self.streaming:
			time.sleep(WAIT_TIME)

			data = self.stream_data.read(BYTES_TO_READ)

			duration = self._create_video_file(data)
			self._create_subtitle_file(data, duration)

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


	def start(self):
		print("Starting Video Streamer:")

		print("Getting Video Stream...", end="")
		stream = self._get_video_stream()
		print("Success!")

		print("Opening stream...", end="")
		data = stream.open()
		print("Success!")

		print("Starting stream worker...", end="")
		self.worker = _StreamWorker(self.buffer, data, self.user_dir, self)
		self.worker.start()
		print("Success!")

	def stop(self):
		self.worker.stop()
