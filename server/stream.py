from streamlink import Streamlink
import server.speechtotext
from ffmpy import FFmpeg

session = Streamlink()
streams = session.streams("https://www.twitch.tv/pazos64")

fd = streams['audio_only'].open()
f = open("audio.ts", "ab")

for i in range(1, 10):
    data1 = fd.read(float('inf'))
    f.write(data1)
    print("Written to file")

f.close()

ff = FFmpeg(
    inputs={'audio.ts': ['-acodec', 'copy']},
    outputs={'audio.wav': ['-vodec', 'copy']}
)

print(ff.cmd)

##with open("audio.wav", "r") as f:
##	content = f.read()

#print(speechtotext.speech_to_text(content, 48000, "es"))

fd.close()
