const io = require('socket.io-client');
// const socket = io('https://polyglot-livesubtitles.herokuapp.com/streams')
const socket = io('http://localhost:8000/streams');

var video = document.getElementById('video');

var button = document.getElementById('disconnect_button');
var button360 = document.getElementById('360_button');
var button480 = document.getElementById('480_button');
var button720 = document.getElementById('720_button');

var buttonEng = document.getElementById('eng_button');
var buttonEsp = document.getElementById('esp_button');
var buttonFrn = document.getElementById('frn_button');

var hls = null;

button.onclick = function() {
    socket.disconnect();
    hls.destroy();
    console.log("Disconnected");
}

button360.onclick = function() {
    hls.destroy();
    console.log("Quality change: 360p");
    socket.emit('quality', {quality:'360p'})
}

button480.onclick = function() {
    hls.destroy();
    console.log("Quality change: 480p");
    socket.emit('quality', {quality:'480p'})
}

button720.onclick = function() {
    hls.destroy();
    console.log("Quality change: 720p");
    socket.emit('quality', {quality:'720p'})
}

buttonEng.onclick = function() {
    socket.emit('language', {sub_lang: 'en'});
}
console.log(socket);

buttonEsp.onclick = function() {
    socket.emit('language', {sub_lang: 'es'});
}

buttonFrn.onclick = function() {
    socket.emit('language', {sub_lang: 'fr'});
}

console.log(socket);

var video = document.getElementById('video');

socket.on('connect', function() {
    console.log("Socket connected");
});

socket.on('server-ready', function() {
    socket.emit('stream', {url: "https://www.youtube.com/watch?v=JsLeCN1U8Eo", lang: "en-GB"})
});

socket.on('progress', function(data) {
    console.log("PROGRESS UPDATE");
})

socket.on('stream-response', function(data) {
    console.log("Recieved stream-response");
    var json = JSON.parse(data);

    if (json.media == "") {
        return;
    }

    var manifest_url = json.media;

    if (Hls.isSupported()) {
        console.log("Hls Supported. Got manifest url: " + manifest_url);

        var hls = new Hls({debug:true});

        // video.addEventListener('error', function() {
        //     console.log("*** ERROR ON VIDEO *** KILLING HLS ***")
        //     hls.destroy();
        // });

        hls.on(Hls.Events.ERROR, function(event, data) {
            if (data.type == Hls.ErrorTypes.MEDIA_ERROR) {
                switch (data.details) {
                    case Hls.ErrorDetails.BUFFER_APPENDING_ERROR:
                    case Hls.ErrorDetails.BUFFER_APPEND_ERROR:
                        console.log("HLS IS BROKE");
                        break;
                    default:
                        console.log("Other media error of type: " + data.details);
                }
            }
        });

        console.log("Loading manifest url...");
        hls.loadSource(manifest_url);
        console.log("Attatching Media...")
        hls.attachMedia(video);

        hls.on(Hls.Events.MANIFEST_PARSED, function (event, data) {
            console.log("Manifest Loaded");
        });
    }

});
