import unittest
from unittest.mock import Mock, MagicMock, patch, ANY
from server.stream import VideoStreamer, _StreamWorker, QUALITY_INFO
from server.playlist import HLSPlaylist
import streamlink

class VideoStreamerTests(unittest.TestCase):

	def test_start(self):
		stream_url = "http://www.example.com/video/stream1"
		language = "en-GB"
		user = "test_user"
		credentials = None

		streamer = VideoStreamer(stream_url, language, user, credentials)

		stream_mock = Mock()
		data_mock = Mock()

		stream_mock.open.return_value = data_mock
		stream_dict = {'best':stream_mock}

		with patch('streamlink.streams', return_value=stream_dict) as mock_streams:
			with patch('server.playlist.HLSPlaylist.__init__', return_value=None) as playlist_const_mock:
				with patch('server.stream._StreamWorker') as StreamWorker_Mock:

					(bytes_to_read, wait_time) = QUALITY_INFO['best']

					progress_mock = MagicMock()
					streamer.start(progress_mock)

					progress_mock.assert_called_with(user)
					StreamWorker_Mock.assert_called_with(data_mock, bytes_to_read, wait_time,\
						language, streamer.sub_language, user, ANY, credentials)

	def test_stop(self):
		streamer = VideoStreamer(None, None, None, None)
		worker = Mock()

		streamer.worker = worker
		streamer.stop()

		worker.stop.assert_called_with()
		worker.join.assert_called_with()

	def test_update_sub_language(self):
		streamer = VideoStreamer(None, None, None, None)
		worker = Mock()
		new_lang = 'fr'

		streamer.worker = worker
		streamer.update_sub_language(new_lang)

		worker.update_language.assert_called_with(new_lang)

	def test_update_quality(self):
		streamer = VideoStreamer(None, None, None, None)
		worker = Mock()
		new_quality = 'worst'

		with patch.object(VideoStreamer, 'start') as start_mock:
			with patch.object(VideoStreamer, 'stop') as stop_mock:
				streamer.update_quality(new_quality)

				streamer.stop.assert_called_with()
				streamer.start.assert_called_with(streamer.progress_callback, new_quality)

class StreamWorkerTests(unittest.TestCase):

	def setUp(self):
		stream_data = Mock()
		bytes_to_read = 1
		wait_time = 1
		language = 'en-GB'
		sub_language = 'en'
		user = 'test_user'
		playlist = Mock()
		credentials = Mock()

		self.worker = _StreamWorker(stream_data, bytes_to_read, wait_time, language, sub_language, \
			user, playlist, credentials)

	def test_update_language(self):
		new_lang = 'en-GB'
		self.worker.update_language(new_lang)

		self.assertEqual(self.worker.sub_language, new_lang)

	def test_get_duration(self):
		video_file = "file.ts"

		with patch('subprocess.check_output') as subprocess_mock:
			self.worker._get_duration(video_file)

			subprocess_mock.assert_called_with(["ffmpeg -i " + video_file + " 2>&1 | grep 'Duration'"], shell=True)
			subprocess_mock.return_value.decode.assert_called_with('ascii')

	# @patch('os.remove')
	# @patch('server.playlist')
	# @patch('webvtt.WebVTT')
	# @patch('server.speechtotext')
	# @patch('server.iptotime')
	# @patch('subprocess.check_output')
	# @patch('io.BytesIO')
	# @patch('wave.open')
	# @patch('ffmpy.FFmpeg.run')
	# @patch('builtins.open')
	# def test_run(self, mock_open, mock_ffmpeg_run, wave_open, bytesIO_mock, subprocess_mock, ip_time_mock, speech_mock, webvtt_mock, playlist_mock, remove_mock):


	# 	worker.run()

	# 	# stream_data.read.assert_called_with(bytes_to_read)
	# 	# mock_open.assert_called_with("Hello")
	# 	# mock_ffmpeg_run.assert_called_with()
	# 	# mock_wave_open.assert_called_with("hello", 'rb')
	# 	# mock_wave_open.return_value.getframerate.assert_called_with()
	# 	# mock_open.assert_called_with("hello2")












if __name__ == '__main__':
	unittest.main()