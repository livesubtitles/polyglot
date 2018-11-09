const video = document.getElementById('video');
console.log(video);

var videoBuffer = [];
var append = true;

// ---- Media Source Stuff ---- //
var sourceBuffer = null;
var mediaSource = new MediaSource();
video.src = URL.createObjectURL(mediaSource);

mediaSource.addEventListener("sourceopen", function() {
    sourceBuffer = mediaSource.addSourceBuffer('video/mp4; codecs="avc1.7a000d,mp4a.40.2"');
    
    sourceBuffer.onupdateend = function() {
    	if (!videoBuffer) {
    		append = true;
    	} else {
    		var data = videoBuffer.shift();
    		if (data == null) {
    			append = true;
    			return;
    		}

        	sourceBuffer.appendBuffer(data);
        }
    }
});

// ---- Socket stuff ---- //
const io = require('socket.io-client');
const socket = io('http://localhost:8000/stream')

socket.on('connect', function() {
    console.log("Socket connected");
    socket.emit('stream', {url: "https://www.youtube.com/watch?v=mV8jp1N2fSw", lang: "es-ES"})
});

socket.on('stream-response', function(data) {
	console.log("Recieved stream-response");
	var json = JSON.parse(data);

	if (json.video == "") {
		socket.emit('ready');
		return;
	}

	var video_array = JSON.parse(json.video)["py/seq"];
	console.log(video_array);

	var blob = new Blob(video_array);

	video.src = URL.createObjectURL(blob);

	// videoBuffer.push(video_array);

	// if (append) {
	// 	sourceBuffer.appendBuffer(videoBuffer.shift());
	// 	append = false;
	// }
});