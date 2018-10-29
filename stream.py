import io
import subprocess
import streamlink
import server.speechtotext as stt
import server.translate as trn
from ffmpy import FFmpeg

def create_wav_from_stream(stream_url):

	available_streams = streamlink.streams(stream_url)
	try:
		audio_stream = available_streams['audio_only']
	except KeyError:
		#Handle video using available_streams['worst']
		exit()

	stream_data = audio_stream.open()

	with open("audio.ts", "ab") as f:
		for i in range(1, 5):
			f.write(stream_data.read(100000))

	stream_data.close()

	FFmpeg(
    	inputs={'audio.ts': ['-ac', '1']},
    	outputs={'audio.wav': ['-ac', '1']}
	).run()

	with open("audio.wav", "rb") as f:
		content = f.read()

	wav_mem_file = io.BytesIO(content)

	return wav_mem_file

	output = subprocess.check_output('ffprobe -v error -show_entries stream=sample_rate -of default=noprint_wrappers=1 audio.wav', shell=True)
	sample_rate = output.decode('utf-8').split('=')[1]

	text = stt.speech_to_text(wav_mem_file, sample_rate, stt.detect_language(wav_mem_file))
