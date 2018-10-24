let vid = document.getElementsByTagName("video")[0];
let track = vid.addTextTrack("captions", "English", "en");
track.mode = "showing";

let MAX_LENGTH = 70;
let lorem = "Lorem ipsum dolor sit amet"
function addSubtitles(text) {
  let start = 1;
  let end = 100000;
  var prev = "";
  if (track && track.activeCues && track.activeCues.length > 0) {
    // if (track.activeCues[0].text.length + text.length <= MAX_LENGTH) {
    //   prev = track.activeCues[0].text + " ";
    // }
    track.removeCue(track.activeCues[0]);
  }
  track.addCue(new VTTCue(start, end, prev + text));
}


let stream = vid.captureStream();
let audioctx = new AudioContext();
let mediaStreamNode = audioctx.createMediaStreamSource(stream);
let numOfBufferedChunks = 0;
let buffersSoFar = "";
// create a script processor with input of size 16384, one input (the video) and one output (the audioctx.destination)
let scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);
scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {
  if (!vid.paused) {
    if (numOfBufferedChunks == 0) {
      buffersSoFar = audioProcessingEvent.inputBuffer;
    } else {
      // merge the previous buffers with the new one
      let mergedBuffer = audioctx.createBuffer(1, buffersSoFar.length + audioProcessingEvent.inputBuffer.length, audioProcessingEvent.inputBuffer.sampleRate);
      let channel = mergedBuffer.getChannelData(0);
      channel.set(buffersSoFar.getChannelData(0), 0);
      channel.set(audioProcessingEvent.inputBuffer.getChannelData(0), buffersSoFar.length);
      buffersSoFar = mergedBuffer;
   }
    numOfBufferedChunks++;
    if (numOfBufferedChunks == 10) {
      numOfBufferedChunks = 0;
      lang = 'el-GR'
      // Send request to backend
      let request = "{\"audio\":" + "[]" + ", \"sampleRate\": " + buffersSoFar.sampleRate + ", \"lang\":\"" + lang + "\"}";
      let jsonRequest = JSON.parse(request);
      for (let i = 0; i < buffersSoFar.getChannelData(0).length; i++) {
        jsonRequest.audio.push(buffersSoFar.getChannelData(0)[i]);
      }
      request = JSON.stringify(jsonRequest);
      let url = "http://127.0.0.1:5000/subtitle"
      fetch(url, {method: 'post',
            headers: {
              "Content-Type": "application/json; charset=utf-8",
            },
          body: request})
      .then(
        function(response) {
          if (response.status !== 200) {
            console.log('Looks like there was a problem. Status Code: ' +
              response.status);
            return;
          }
          response.json().then(function(data) {
            console.log(data.subtitle);
            addSubtitles(data.subtitle);
          });
        });
    }
  }
};
mediaStreamNode.connect(scriptProcessingNode);
scriptProcessingNode.connect(audioctx.destination);
