class HLSPlaylist(object):

	_MASTER_STUB = '#EXTM3U\n#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="English",URI="subtitles.m3u8",LANGUAGE="en"\n#EXT-X-STREAM-INF:BANDWIDTH=200000,RESOLUTION=480x360,SUBTITLES="subs"\nplaylist.m3u8\n'
	_PLAYLIST_STUB = '#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:10\n#EXT-X-MEDIA-SEQUENCE:0\n'

	_VIDEO_FILE_NAME = 'segment'
	_VIDEO_FILE_EXT  = '.ts'
	_SUBTITLE_FILE_NAME = 'subtitle'
	_SUBTITLE_FILE_EXT  = '.vtt'

	def __init__(self, user):
		self.master_playlist_path   = 'streams/' + user + '/masterplaylist.m3u8'
		self.video_playlist_path    = 'streams/' + user + '/playlist.m3u8'
		self.subtitle_playlist_path = 'streams/' + user + '/subtitles.m3u8'

		with open(self.master_playlist_path, 'w') as f:
			f.write(self._MASTER_STUB)

		with open(self.video_playlist_path, 'w') as f:
			f.write(self._PLAYLIST_STUB)

		with open(self.subtitle_playlist_path, 'w') as f:
			f.write(self._PLAYLIST_STUB)

	def get_master(self):
		return self.master_playlist_path

	def get_video(self):
		return self.video_playlist_path

	def get_subtitle(self):
		return self.subtitle_playlist_path

	def update_all(self, count, duration):
		new_video_file = self._VIDEO_FILE_NAME + str(count) + self._VIDEO_FILE_EXT
		new_subs_file  = self._SUBTITLE_FILE_NAME + str(count) + self._SUBTITLE_FILE_EXT

		self._update(self.subtitle_playlist_path, new_subs_file, duration)
		self._update(self.video_playlist_path, new_video_file, duration)

	def _update(self, playlist_path, file_name, duration):
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
