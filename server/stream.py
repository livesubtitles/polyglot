import io
import os
import shutil
import subprocess
import streamlink
import wave
import sys
import time
import json
import subprocess
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
INPUT_FILE		= "segment"
EXTENSION 		= ".ts"
OUTPUT_WAV_FILE = "temp/audio.wav"

# Nukes the temp directory and generates a fresh one
def _clearTempFiles():
	if os.path.isdir('temp'):
		shutil.rmtree('temp')
	os.makedirs('temp')

class _StreamWorker(Thread):
	def __init__(self, buff, stream_data, user_dir, callback, video_streamer):
		self.buff = buff
		self.stream_data = stream_data
		self.user_dir = user_dir
		self.streaming = True
		self.count = 0
		self.callback = callback
		self.start_sending = False
		self.time_so_far = 0
		self.video_streamer = video_streamer
		Thread.__init__(self)

	def _update_playlist(self, video_file):
		playlist_path = self.user_dir + '/playlist.m3u8'

		if not os.path.isfile(playlist_path):
			print("Playlist not found, exiting...")
			raise Exception

		with open(playlist_path, "r") as f:
			lines = f.readlines()

		sequence_no = int(lines[3].split(':')[1])

		lines[3] = '#EXT-X-MEDIA-SEQUENCE:' + str(sequence_no) + '\n'

		if (sequence_no + 1 >= 4 and len(lines) >= 7):
			lines = lines[0:4] + lines[7:]
			lines[3] = '#EXT-X-MEDIA-SEQUENCE:' + str(sequence_no + 1) + '\n'
			if (not self.start_sending):
				self.start_sending = True
		print(lines)


		with open(playlist_path, "w+") as f:
			f.writelines(lines)
			if not sequence_no == 0:
				f.write('#EXT-X-DISCONTINUITY\n')
			f.write('#EXTINF:20.0000,\n')
			f.write(video_file + '\n')

		# with open(self.user_dir + '/subtitleSegment1.webvtt', "w") as f:
		# 	f.write("WEBVTT\n")
		# 	f.write("\n")
		# 	f.write('00:00:00.00-->00:00:10.00 align:start\n')
		# 	f.write('This is a caption\n')

		segment_duration = self.get_duration_time(self.user_dir + "/" + video_file)
		# subtitle_playlist_path = self.user_dir + "/subtitles.m3u8"
		# with open(subtitle_playlist_path, "w") as subtitleplaylist:
		# 	subtitleplaylist.write('#EXTM3U\n')
		# 	subtitleplaylist.write('#EXT-X-TARGETDURATION:20\n')
		# 	subtitleplaylist.write('#EXT-X-VERSION:3\n')
		# 	subtitleplaylist.write('#EXT-X-MEDIA-SEQUENCE:1\n')
		# 	subtitleplaylist.write('#EXTINF:20,\n')
		# 	subtitleplaylist.write('subtitleSegment1.webvtt\n')

		master_playlist_path = self.user_dir + "/masterplaylist.m3u8"
		# with open(master_playlist_path, "w") as masterplaylist:
		# 	masterplaylist.write('#EXTM3U\n')
		# 	masterplaylist.write('#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-\n')
		# 	masterplaylist.write('ID="subs",NAME="English",DEFAULT=NO,FORCED=NO,URI="subtitles.m3u8",LANGUAGE="en"\n')
		# 	masterplaylist.write('#EXT-X-STREAM-INF:BANDWIDTH=1118592,CODECS="mp4a.40.2,\n')
		# 	masterplaylist.write('avc1.64001f",RESOLUTION=640x360,SUBTITLES="subs"\n')
		# 	masterplaylist.write('playlist.m3u8')



		# if (self.start_sending):
		# 	self.callback()

	def get_duration_time(self, video_file):
		duration = subprocess.check_output(["ffmpeg -i " + video_file +   " 2>&1 | grep 'Duration'"], shell=True)
		duration_time = duration.decode('ascii').split("Duration: ")[1].split(',')[0]
		return float(duration_time.split(":")[2])
		print("Segment duration time: " + duration_time)

	def process(self, audio, sample_rate, lang, raw_pcm=False):
		if lang == '':
			lang = detect_language(audio)

		transcript = get_text_from_pcm(audio, sample_rate, lang) if raw_pcm else \
		get_text(audio, sample_rate, lang)
		translated = translate(transcript, 'en', lang.split('-')[0])
		response = {}
		response["subtitle"] = translated
		response["lang"] = lang
		return json.dumps(response)


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
				audio_data = self.video_streamer._extract_audio(path + video_file)
			except Exception as e:
				raise Exception("FFMPEG error")

			self.video_streamer._set_sample_rate()

			print(self.process(io.BytesIO(audio_data), self.video_streamer.get_sample_rate(), "es-ES", False))

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
	def __init__(self, stream_url, user_dir, callback):
		self.stream_url = stream_url
		self.user_dir = user_dir
		self.buffer = queue.Queue()
		self.sample_rate = None
		self.worker = None
		self.callback = callback

	# def get_data(self, num_segments=5):
	# 	video_data = self.buffer.get()
	#
	# 	for i in range(1, num_segments):
	# 		video_data += self.buffer.get()
	#
	# 	video_file = INPUT_FILE + str(self.count) + EXT
	# 	self.count += 1
	#
	# 	with open(video_file, "ab") as f:
	# 		f.write(video_data)
	#
	# 	try:
	# 		audio_data = self._extract_audio(video_file)
	# 	except Exception as e:
	# 		raise Exception("FFMpeg Error")
	#
	# 	self._set_sample_rate()
	#
	# 	return (bytearray(video_data), io.BytesIO(audio_data))
	#
	def get_sample_rate(self):
		return self.sample_rate
	#
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

		print("Getting Video Stream...", end="")
		stream = self._get_video_stream()

		if stream == None:
			raise Exception("Streamlink Unavailable")
		print("Success!")

		print("Opening stream...", end="")
		data = stream.open()
		print("Success!")

		print("Starting stream worker...", end="")
		self.worker = _StreamWorker(self.buffer, data, self.user_dir, self.callback, self)
		self.worker.start()
		print("Success!")

	def stop(self):
		self.worker.stop()
