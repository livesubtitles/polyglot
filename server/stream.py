import io
import os
import shutil
import subprocess
import streamlink
import wave
import sys
import time
from math import ceil
from datetime import timedelta, datetime
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
from server.iptotime import *

QUALITY_INFO = {'worst': (500000, 6),
                '144p': (500000, 6),
                '240p': (800000, 8),
                '360p': (1000000, 10),
                '480p': (2000000, 10),
                '720p': (3000000, 10),
                '1080p': (4000000, 10),
                'best': (4000000, 10),
                'default': (1000000, 10)}

SUB_SEG_SIZE  = 10

VID_INPUT_FILE  = "segment"
SUB_INPUT_FILE  = "subtitle"
VID_EXTENSION   = ".ts"
SUB_EXTENSION   = ".vtt"
OUTPUT_WAV_FILE = "/audio.wav"

############# Logging utility #############
def current_time():
    return int(round(time.time() * 1000))
###########################################

class _StreamWorker(Thread):
    def __init__(self, stream_data, bytes_to_read, wait_time, language, \
                        sub_language, user, playlist, credentials):

        self.stream_data = stream_data
        self.user = user
        self.user_dir = 'streams/' + user
        self.user = user
        self.streaming = True
        self.count = 0
        self.current_time = 0
        self.sample_rate = 0
        self.pipeline_wait = 0
        self.bytes_to_read = bytes_to_read
        self.wait_time = wait_time
        self.credentials = credentials
        self.playlist = playlist
        self.language = language
        self.sub_language = sub_language
        Thread.__init__(self)

    def update_language(self, new_language):
        self.sub_language = new_language

    def _get_duration(self, video_file):
        output = subprocess.check_output(["ffmpeg -i " + video_file + " 2>&1 | grep 'Duration'"], shell=True)
        duration = output.decode('ascii').split("Duration: ")[1].split(',')[0]
        return float(duration.split(":")[2])

    def _extract_audio(self, file_name):
        FFmpeg(
            inputs={file_name:['-hide_banner', '-loglevel', 'panic', '-y']},
            outputs={(self.user_dir + OUTPUT_WAV_FILE):['-af', 'aresample=async=1', '-ac', '1', '-vn', '-f', 'wav']}
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

        print("Fetching subtitles...", end="")
        start_time = current_time()

        transcript = get_text_from_pcm(audio, sample_rate, self.language, self.sub_language) if raw_pcm else \
                     get_text(audio, sample_rate, self.language, self.credentials, self.sub_language)

        end_time = current_time()
        wait_time_ms = end_time - start_time

        self.pipeline_wait = int(wait_time_ms / 1000)
        print("Success! Time taken: " + str(wait_time_ms) + "ms")

        return transcript

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

    def _create_subtitle_file(self, data, audio_data, duration):
        file_path = self._get_next_filepath(subtitle=True)
        subtitles = self._get_subtitle(audio_data, self.sample_rate)

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

    def _remove_file(self, file):
        if file != "":
            path = self.user_dir + "/" + file
            print("Removing file: " + path)
            os.remove(path)

    def _cleanup_files(self, removed):
        (removed_vid, removed_sub) = removed
        self._remove_file(removed_vid)
        self._remove_file(removed_sub)

    def run(self):
        time.sleep(self.wait_time)

        while self.streaming:
            data = self.stream_data.read(self.bytes_to_read)

            video_path = self._create_video_file(data)

            audio_data = self._extract_audio(video_path)
            duration = self._get_duration(video_path)

            audio_path = self._create_subtitle_file(data, audio_data, duration)

            removed = self.playlist.update_all(self.count, duration)
            self._cleanup_files(removed)

            self.count += 1
            time.sleep(max(0, self.wait_time - self.pipeline_wait))

        self.stream_data.close()

    def stop(self):
        self.streaming = False


class VideoStreamer(object):
    def __init__(self, stream_url, language, user, credentials):
        self.stream_url = stream_url
        self.language = language
        self.user = user
        self.credentials = credentials
        self.quality = 'best'
        self.sub_language = 'en'
        self.worker = None
        self.available_streams = None
        self.progress_callback = None

    def _get_video_stream(self):
        try:
            self.available_streams = streamlink.streams(self.stream_url)
        except Exception:
            raise Exception("Streamlink Unavailable")

        print("Available Streams: " + str(self.available_streams))

        if self.quality not in self.available_streams:
            print("Could not find " + self.quality + " stream")
            raise Exception("Streamlink Unavailable")

        return self.available_streams[self.quality]

    def get_supported_qualities(self):
        return list(self.available_streams.keys())

    def update_sub_language(self, new_language):
        if new_language == self.sub_language:
            return

        print("!Subtitle Language Update!")

        print("Updating Stream Worker...", end="")
        self.worker.update_language(new_language)
        self.sub_language = new_language
        print("Success!")

    def update_quality(self, new_quality):
        if new_quality == self.quality:
            return

        print("!Stream Quality Update!")

        print("Stopping worker...", end="")
        self.stop()
        print("Success!")

        return self.start(self.progress_callback, new_quality)

    def start(self, progress_callback, quality='best', sub_language='en'):
        print("Starting Video Streamer with quality: " + quality)
        self.quality = quality
        self.sub_language = sub_language
        self.progress_callback = progress_callback

        progress_callback(self.user)

        print("Getting Video Stream...", end="")
        stream = self._get_video_stream()
        print("Success!")

        progress_callback(self.user)

        print("Opening stream...", end="")
        data = stream.open()
        print("Success!")

        print("Creating playlist...", end="")
        playlist = HLSPlaylist(self.user)
        print("Success!")

        quality_key = self.quality if (self.quality in QUALITY_INFO) else 'default'

        (bytes_to_read, wait_time) = QUALITY_INFO[quality_key]

        print("Starting stream worker...", end="")
        self.worker = _StreamWorker(data, bytes_to_read, wait_time, self.language,
            sub_language, self.user, playlist, self.credentials)
        self.worker.start()
        print("Success!")

        progress_callback(self.user)

        return playlist

    def check_if_available(self, progress_callback, quality='best', sub_language='en'):
        print("Starting Video Streamer with quality: " + quality)
        self.quality = quality
        self.sub_language = sub_language
        self.progress_callback = progress_callback

        progress_callback(self.user)

        print("Getting Video Stream...", end="")
        stream = self._get_video_stream()
        print("Success!")

        progress_callback(self.user)

        print("Opening stream...", end="")
        data = stream.open()
        print("Success!")
        return True

    def stop(self):
        if self.worker != None:
            self.worker.stop()
            self.worker.join()
            self.worker = None
