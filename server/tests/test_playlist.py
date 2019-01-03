import unittest
import responses
import os
import mock
from mock import *
import server.playlist
from server.playlist import *
from pathlib import Path

class TestPlaylist(unittest.TestCase):

    def test_creatingPlaylist(self):
        username = "test_user"
        user_dir = 'streams/' + username
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        playlist = HLSPlaylist(username)

        streams_folder = Path("streams/")
        streams_user_folder = Path("streams/test_user")
        master_playlist_path = Path("streams/test_user/masterplaylist.m3u8")
        video_playlist_path = Path("streams/test_user/playlist.m3u8")
        subtitle_playlist_path = Path("streams/test_user/subtitles.m3u8")

        self.assertEqual(streams_folder.is_dir(), True)
        self.assertEqual(streams_user_folder.is_dir(), True)
        self.assertEqual(master_playlist_path.is_file(), True)
        self.assertEqual(video_playlist_path.is_file(), True)
        self.assertEqual(subtitle_playlist_path.is_file(), True)

        with open(master_playlist_path, 'r') as f:
            self.assertEqual(f.read(), playlist._MASTER_STUB)

        with open(video_playlist_path, 'r') as f:
            self.assertEqual(f.read(), playlist._PLAYLIST_STUB)

        with open(subtitle_playlist_path, 'r') as f:
            self.assertEqual(f.read(), playlist._PLAYLIST_STUB)

        self.assertEqual(playlist.get_master(), "streams/test_user/masterplaylist.m3u8")
        self.assertEqual(playlist.get_video(), "streams/test_user/playlist.m3u8")
        self.assertEqual(playlist.get_subtitle(), "streams/test_user/subtitles.m3u8")

    def test_updateAllPlaylist(self):
        username = "test_user"
        user_dir = 'streams/' + username
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        playlist = HLSPlaylist(username)

        video_playlist_path = Path("streams/test_user/playlist.m3u8")
        subtitle_playlist_path = Path("streams/test_user/subtitles.m3u8")

        playlist.update_all(0, 20)
        playlist.update_all(1, 20)
        playlist.update_all(2, 20)
        playlist.update_all(3, 20)

        expected_sequences_video = ['#EXTINF:20,\n', 'segment0.ts\n', '#EXTINF:20,\n',
        'segment1.ts\n', '#EXTINF:20,\n', 'segment2.ts\n', '#EXTINF:20,\n', 'segment3.ts\n']

        expected_sequences_subtitle = ['#EXTINF:20,\n', 'subtitle0.vtt\n', '#EXTINF:20,\n',
        'subtitle1.vtt\n', '#EXTINF:20,\n', 'subtitle2.vtt\n', '#EXTINF:20,\n', 'subtitle3.vtt\n']

        with open(video_playlist_path, "r") as f:
            lines = f.readlines()
            sequences = lines[4:]
            self.assertEqual(sequences, expected_sequences_video)
        with open(subtitle_playlist_path, "r") as f:
            lines = f.readlines()
            sequences = lines[4:]
            print (sequences)
            self.assertEqual(sequences, expected_sequences_subtitle)

        playlist.update_all(4, 20)

        expected_sequences_video2 = ['#EXTINF:20,\n', 'segment1.ts\n', '#EXTINF:20,\n',
        'segment2.ts\n', '#EXTINF:20,\n', 'segment3.ts\n', '#EXTINF:20,\n', 'segment4.ts\n']

        expected_sequences_subtitle2 = ['#EXTINF:20,\n', 'subtitle1.vtt\n', '#EXTINF:20,\n',
        'subtitle2.vtt\n', '#EXTINF:20,\n', 'subtitle3.vtt\n', '#EXTINF:20,\n', 'subtitle4.vtt\n']

        with open(video_playlist_path, "r") as f:
            lines = f.readlines()
            sequences = lines[4:]
            self.assertEqual(sequences, expected_sequences_video2)
        with open(subtitle_playlist_path, "r") as f:
            lines = f.readlines()
            sequences = lines[4:]
            self.assertEqual(sequences, expected_sequences_subtitle2)

if __name__ == '__main__':
    unittest.main()
