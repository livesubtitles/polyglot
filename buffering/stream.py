from streamlink import Streamlink

session = Streamlink()
streams = session.streams("https://www.twitch.tv/valkia")

fd = streams['audio_only'].open()
f = open("audio.ts", "ab")

for i in range(1, 10):
    data1 = fd.read(float('inf'))
    f.write(data1)
    print("Written to file")

f.close()
fd.close()

