const io = require('socket.io-client');
const socket = io('http://localhost:8000/streams');

console.log(socket);

var video = document.getElementById('video');

socket.on('connect', function() {
    console.log("Socket connected");
});

socket.on('server-ready', function() {
    socket.emit('stream', {url: "https://www.youtube.com/watch?v=XOacA3RYrXk", lang: "es-GB"})
});

socket.on('stream-response', function(data) {
    console.log("Recieved stream-response");
    v = JSON.parse(data);

    if (json.media == "") {
        return;
    }

    var manifest_url = json.media;

    if (Hls.isSupported()) {
        console.log("Hls Supported. Got manifest url: " + manifest_url);

        var hls = new Hls();
        console.log("Loading manifest url...");
        hls.loadSource(manifest_url);
        console.log("Attatching Media...")
        hls.attachMedia(video);
        hls.enableWebVTT(true);

        hls.on(Hls.Events.MANIFEST_PARSED, function (event, data) {
            console.log("Manifest Loaded");
        });

    }

});
