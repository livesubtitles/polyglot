const io = require('socket.io-client');
const sock = io("http://127.0.0.1:5000/");
sock.on('connection', function(res){
  console.log('Connected');
  console.log("Received: " + res);
  console.log(res);
});


let vid = document.getElementsByTagName("video")[0];
let stream = vid.captureStream();
let audioctx = new AudioContext();
let mediaStreamNode = audioctx.createMediaStreamSource(stream);
// create a script processor with input of size 16384, one input (the video) and one output (the audioctx.destination)
let scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);
scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {
  if (!vid.paused) {
    //Send along pipeline
    //Recieve translated text
    //Display Text
    //Handle grouping of chunks
    console.log(audioProcessingEvent);
    sock.emit("audioprocess", {
      channelData: audioProcessingEvent.inputBuffer.getChannelData(0),
      sampleRate: audioProcessingEvent.inputBuffer.sampleRate,
    });
  }
};
mediaStreamNode.connect(scriptProcessingNode);
scriptProcessingNode.connect(audioctx.destination);
