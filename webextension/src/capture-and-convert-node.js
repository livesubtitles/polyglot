let vid = document.getElementsByTagName("video")[0];
let stream = vid.captureStream();
let audioctx = new AudioContext();
let mediaStreamNode = audioctx.createMediaStreamSource(stream);
let numOfBufferedChunks = 0;
let buffersSoFar = "";
// create a script processor with input of size 16384, one input (the video) and one output (the audioctx.destination)
let scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);
scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {
  // some code here, getting the audio and sending it to the APIs
  console.log(audioProcessingEvent);
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
  console.log(numOfBufferedChunks);
  // once 50 audio buffers have been merged send speech-to-text request
  if (numOfBufferedChunks % 50 == 0) {
    numOfBufferedChunks = 0;
    // convert PCM data to wav file required by the API
    var toWav = require('audiobuffer-to-wav');
    var wav = toWav(buffersSoFar);
    // convert wav file to base64 string to send in request
    let audiobase64 = new Buffer(wav).toString('base64');
  let request = "{" +
    "'config': {" +
        "'encoding':'LINEAR16',\n" +
        "'languageCode': 'en-US',\n" +
        "'sampleRateHertz': 44100,\n" +
        "'enableWordTimeOffsets': false\n" +
    "}," +
    "'audio': {" +
      "'content': '" + audiobase64 +
    "'}" +
  "}"
  console.log(request);
  // Send speech-to-text request
  let googleApi = 'https://speech.googleapis.com/v1/speech:recognize?key=AIzaSyBjc_I5U-kPsH_DSab29VZ1GBOoqaQOwy4';
  fetch(googleApi, {method: 'post',
        headers: {
          "Content-Type": "application/json; charset=utf-8"
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
        console.log(data);
      });
    }
  )
  .catch(function(err) {
    console.log('Fetch Error :-S', err);
  });
}

};
mediaStreamNode.connect(scriptProcessingNode);
scriptProcessingNode.connect(audioctx.destination);
