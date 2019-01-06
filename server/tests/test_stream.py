import unittest
from unittest.mock import Mock, MagicMock, patch, ANY, call
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

	def test_get_video_stream_unavailable(self):
		streamer = VideoStreamer(None, None, None, None)

		with patch('streamlink.streams', side_effect=Exception("Streamlink Unavilable")) as streams_mock:
			try:
				streamer._get_video_stream()
			except Exception:
				return

		self.fail("Exception was not thrown")

	def test_get_video_quality_unavailable(self):
		streamer = VideoStreamer(None, None, None, None)

		streamer.quality = '360p'
		available = {'best', 'worst'}

		with patch('streamlink.streams', return_value=available) as streams_mock:
			try:
				streamer._get_video_stream()
			except Exception:
				return

		self.fail("Exception was not thrown")

	def test_stop(self):
		streamer = VideoStreamer(None, None, None, None)
		worker = Mock()

		streamer.worker = worker
		streamer.stop()

		worker.stop.assert_called_with()
		worker.join.assert_called_with()

	def test_stop_no_worker(self):
		streamer = VideoStreamer(None, None, None, None)
		streamer.worker = None
		streamer.stop()

	def test_get_supported_qualities(self):
		streamer = VideoStreamer(None, None, None, None)

		stream_qualities = ['360p', '240p']
		streams = {'360p':None, '240p':None}

		streamer.available_streams = streams
		qualities = streamer.get_supported_qualities()

		self.assertEqual(qualities, stream_qualities)

	def test_update_sub_language(self):
		streamer = VideoStreamer(None, None, None, None)
		worker = Mock()
		new_lang = 'fr'

		streamer.worker = worker
		streamer.update_sub_language(new_lang)

		worker.update_language.assert_called_with(new_lang)

	def test_update_sub_language_not_new(self):
		streamer = VideoStreamer(None, None, None, None)
		worker = Mock()
		new_lang = streamer.sub_language

		streamer.worker = worker
		streamer.update_sub_language(new_lang)

		worker.update_sub_language.assert_not_called()

	def test_update_quality(self):
		streamer = VideoStreamer(None, None, None, None)
		new_quality = 'worst'

		with patch.object(VideoStreamer, 'start') as start_mock:
			with patch.object(VideoStreamer, 'stop') as stop_mock:
				streamer.update_quality(new_quality)

				streamer.stop.assert_called_with()
                streamer.start.assert_called_with(streamer.progress_callback, new_quality)

	def test_update_quality_not_new(self):
		streamer = VideoStreamer(None, None, None, None)
		new_quality = streamer.quality

		with patch.object(VideoStreamer, 'start') as start_mock:
			with patch.object(VideoStreamer, 'stop') as stop_mock:
				streamer.update_quality(new_quality)

				streamer.stop.assert_not_called()
				streamer.start.assert_not_called()

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

    @patch('server.stream._StreamWorker._create_video_file')
    @patch('server.stream._StreamWorker._extract_audio')
    @patch('server.stream._StreamWorker._get_duration')
    @patch('server.stream._StreamWorker._create_subtitle_file')
    @patch('server.stream._StreamWorker._cleanup_files')
    @patch('time.sleep')
    def test_run(self, sleep_mock, *args):

        true_once = Mock()
        true_once.called = False

        def __bool__(self):
            if self.called:
                return False
            else:
                self.called = True
                return True

        true_once.__bool__ = __bool__
        
        self.worker.streaming = true_once
        self.worker.run()
        
        sleep_mock.assert_has_calls([call(self.worker.wait_time)] * 2)
        self.worker.stream_data.close.assert_called_with()

    @patch('io.BytesIO')
    @patch('builtins.open')
    @patch('wave.open')
    @patch('ffmpy.FFmpeg.run')
    @patch('ffmpy.FFmpeg.__init__', return_value=None)
    def test_extract_audio(self, mock_ffmpeg, mock_ffmpeg_run, wave_mock, open_mock, bytesIO_mock):
        file_name = "file.ts"
        output_file = self.worker.user_dir + "/audio.wav"

        self.worker._extract_audio(file_name)

        mock_ffmpeg.assert_called_with(inputs={file_name:ANY}, outputs={output_file:ANY})
        mock_ffmpeg_run.assert_called_with()
        wave_mock.assert_called_with(output_file, 'rb')
        open_mock.assert_called_with(output_file, 'rb')

	@patch('io.BytesIO')
	@patch('builtins.open')
	@patch('wave.open')
	@patch('ffmpy.FFmpeg.run')
	@patch('ffmpy.FFmpeg.__init__', return_value=None)
	def test_extract_audio_sample_rate_set(self, mock_ffmpeg, mock_ffmpeg_run, wave_mock, open_mock, bytesIO_mock):
		file_name = "file.ts"
		output_file = self.worker.user_dir + "/audio.wav"

		self.worker.sample_rate = 1

		self.worker._extract_audio(file_name)

		mock_ffmpeg.assert_called_with(inputs={file_name:ANY}, outputs={output_file:ANY})
		mock_ffmpeg_run.assert_called_with()
		wave_mock.assert_not_called()
		open_mock.assert_called_with(output_file, 'rb')

	def test_get_subtitle(self):
		self.worker.language = ''

		audio = Mock()
		sample_rate = Mock()
		s_lang = self.worker.sub_language
		cred = self.worker.credentials

		with patch('server.stream.detect_language') as lang_detect_mock:
			with patch('server.stream.get_text') as get_text_mock:
				with patch('server.stream.get_text_from_pcm') as get_text_pcm_mock:
					self.worker._get_subtitle(audio, sample_rate, False)
					lang_detect_mock.assert_called_with(audio)
					lang = lang_detect_mock.return_value
					get_text_mock.assert_called_with(audio, sample_rate, lang, cred, s_lang)

					self.worker._get_subtitle(audio, sample_rate, True)
					get_text_pcm_mock.assert_called_with(audio, sample_rate, lang, s_lang)

	def test_create_video_file(self):
		data = Mock()

		next_file = self.worker._get_next_filepath(False)

		with patch('server.stream._StreamWorker._get_next_filepath', return_value=next_file) as next_file_mock:
			with patch('builtins.open') as open_mock:
				self.worker._create_video_file(data)

				open_mock.assert_called_with(next_file, "wb")

	def test_create_subtitle_file_nosubs(self):
		data = Mock()
		audio_data = Mock()
		duration = Mock()

		next_file = self.worker._get_next_filepath(True)

		with patch('server.stream._StreamWorker._get_next_filepath', return_value=next_file) as next_file_mock:
			with patch('server.stream._StreamWorker._get_subtitle') as subtitle_mock:
				with patch('webvtt.WebVTT') as webvtt_mock:
					with patch('builtins.open') as open_mock:
						self.worker._create_subtitle_file(data, audio_data, duration)

						subtitle_mock.assert_called_with(audio_data, self.worker.sample_rate)
						open_mock.assert_called_with(next_file, 'w')


	def test_create_subtitle_file(self):
		data = Mock()
		audio_data = Mock()
		duration = 10

		next_file = self.worker._get_next_filepath(True)

		with patch('server.stream._StreamWorker._get_next_filepath', return_value=next_file) as next_file_mock:
			with patch('server.stream._StreamWorker._get_subtitle', return_value="hello") as subtitle_mock:
				with patch('webvtt.WebVTT') as webvtt_mock:
					with patch('builtins.open') as open_mock:
						self.worker._create_subtitle_file(data, audio_data, duration)

						subtitle_mock.assert_called_with(audio_data, self.worker.sample_rate)
						open_mock.assert_called_with(next_file, 'w')

	def test_stop(self):
		self.worker.stop()

	def test_cleanup_files(self):
		removed = ("video.ts", "subtitle.ts")

		calls = [call("streams/test_user/video.ts"), call("streams/test_user/subtitle.ts")]

		with patch('os.remove') as remove_mock:
			self.worker._cleanup_files(removed)

			remove_mock.assert_has_calls(calls)
		
	def test_remove_file_empty_path(self):
		with patch('os.remove') as remove_mock:
			self.worker._remove_file("")

			remove_mock.assert_not_called()

if __name__ == '__main__':
        unittest.main()
