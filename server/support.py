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

def isStreamLinkSupported(url):
	global loaded_files
	global supported_websites
	if (not loaded_files):
		supported_websites = set(line.strip() for line in open('supported_websites'))
		loaded_files = True
	return extractPage(url) in supported_websites
