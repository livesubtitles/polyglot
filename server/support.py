import streamlink

from server.stream import *
def extractPage(url):
    first = "www."
    last = "."
    try:
        start = url.index( first ) + len( first )
        end = url.index( last, start )
        return url[start:end]
    except ValueError:
        return ""

loaded_files = False;
supported_websites = []

def isStreamLinkSupported(url, websites_list):
    global loaded_files
    global supported_websites
    if (not loaded_files):
        with open(websites_list) as f:
            supported_websites = set(line.strip() for line in f)
        loaded_files = True
    return extractPage(url) in supported_websites

def dummyCallback(arg):
    return None

def streamLinkFails(url):
    streamer = VideoStreamer(url, 'es-ES', 123, None)
    try:
        playlist = streamer.check_if_available(dummyCallback)
    except Exception as exe:
        print("VideoStreamer raised an exception: " + str(exe))
        return False
    return True
