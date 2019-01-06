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

# class StreamWorkerTests(unittest.TestCase):

# 	def test_run(self):
		





if __name__ == '__main__':
	unittest.main()