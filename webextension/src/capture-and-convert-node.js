let vid = document.getElementsByTagName("video")[0];
let stream = vid.captureStream();
let audioctx = new AudioContext();
let mediaStreamNode = audioctx.createMediaStreamSource(stream);
// create a script processor with input of size 16384, one input (the video) and one output (the audioctx.destination)
let scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);
scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {
  // some code here, getting the audio and sending it to the APIs
  console.log(audioProcessingEvent);
  var toWav = require('audiobuffer-to-wav');
  var wav = toWav(audioProcessingEvent.inputBuffer);
  var binary = '';
  var bytes = new Uint8Array(wav);
  var len = bytes.byteLength;
  for (var i = 0; i < len; i++) {
      binary += String.fromCharCode( bytes[ i ] );
  }
  // console.log(window.btoa(binary));
  // console.log(buffer);
  // let audiobase64 = window.btoa(binary);
  let audiobase64 = new Buffer(wav).toString('base64');
  console.log(audiobase64);
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

};
mediaStreamNode.connect(scriptProcessingNode);
scriptProcessingNode.connect(audioctx.destination);
