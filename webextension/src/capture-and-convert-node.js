let vid = document.getElementsByTagName("video")[0];
let stream = vid.captureStream();
let audioctx = new AudioContext();
let mediaStreamNode = audioctx.createMediaStreamSource(stream);
let numOfBufferedChunks = 0;
let buffersSoFar = "";
// Enter an API key from the Google API Console:
//   https://console.developers.google.com/apis/credentials
const apiKey = "AIzaSyBjc_I5U-kPsH_DSab29VZ1GBOoqaQOwy4";

// load script
async function loadScript(url) {
  let response = await fetch(url);
  let script = await response.text();
  eval(script);
}

let scriptUrl = 'https://ajax.googleapis.com/ajax/libs/jquery/2.0.0/jquery.min.js'
loadScript(scriptUrl);

// Set endpoints
const endpoints = {
  translate: "",
  detect: "detect",
  languages: "languages"
};


// Abstract API request function
function makeApiRequest(endpoint, data, type, authNeeded) {
  url = "https://www.googleapis.com/language/translate/v2/" + endpoint;
  url += "?key=" + apiKey;

  // If not listing languages, send text to translate
  if (endpoint !== endpoints.languages) {
    url += "&q=" + encodeURI(data.textToTranslate);
  }
  // If translating, send target and source languages
  if (endpoint === endpoints.translate) {
    url += "&target=" + data.targetLang;
    url += "&source=" + data.sourceLang;
  }

  // Return response from API
  return $.ajax({
    url: url,
    type: type || "GET",
    data: data ? JSON.stringify(data) : "",
    dataType: "json",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json"
    }
  });
}

// Translate
function translate(data) {
  makeApiRequest(endpoints.translate, data, "GET", false).then(function(
    resp
  ) {
    $(".target").text(resp.data.translations[0].translatedText);
    $("h2.detection-heading").hide();
    $("h2.translation-heading, p").show();
    console.log(resp.data.translations[0].translatedText);
  });
}
// On document ready
$(function() {
  window.makeApiRequest = makeApiRequest;
});
// create a script processor with input of size 16384, one input (the video) and one output (the audioctx.destination)
let scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);
scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {
  // some code here, getting the audio and sending it to the APIs
  // console.log(audioProcessingEvent);
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
  // console.log(numOfBufferedChunks);
  // once 50 audio buffers have been merged send speech-to-text request
  if (numOfBufferedChunks == 10) {
    numOfBufferedChunks = 0;
    // convert PCM data to wav file required by the API
    var toWav = require('audiobuffer-to-wav');
    var wav = toWav(buffersSoFar);
    // convert wav file to base64 string to send in request
    let audiobase64 = new Buffer(wav).toString('base64');
  let request = "{" +
    "'config': {" +
        "'encoding':'LINEAR16',\n" +
        "'languageCode': 'fr-FR',\n" +
        "'sampleRateHertz': 44100,\n" +
        "'enableWordTimeOffsets': false\n" +
    "}," +
    "'audio': {" +
      "'content': '" + audiobase64 +
    "'}" +
  "}"
  // console.log(request);
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
        // console.log(data);
        if (data.results.length > 0) {
          let transcript = data.results[0].alternatives[0].transcript;
          console.log(data.results[0].alternatives[0].transcript);
          let t = {
             sourceLang: "fr",
             targetLang: "en",
            textToTranslate: transcript
           }
           let resp = translate(t);
           // console.log(resp);
        }
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
