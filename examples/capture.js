// open a video on youtube and copy this code into your console (Chrome)
let vid = document.getElementsByTagName("video")[0];
let stream = vid.captureStream();
let audioctx = new AudioContext();
let mediaStreamNode = audioctx.createMediaStreamSource(stream);
// create a script processor with input of size 4096, one input (the video) and one output (the audioctx.destination)
let scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);
scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {
  // some code here, getting the audio and sending it to the APIs
  console.log(audioProcessingEvent);
};
mediaStreamNode.connect(scriptProcessingNode);
scriptProcessingNode.connect(audioctx.destination);
