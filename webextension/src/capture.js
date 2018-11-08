/* Url definitions */
const localUrl = "http://127.0.0.1:8000";
const herokuUrl = "https://polyglot-livesubtitles.herokuapp.com";
const baseUrl = localUrl;
const captureEndpoint = "/subtitle"
const streamEndpoint = "/stream"

/* Definitions for capture and stream requests */
let vid = document.getElementsByTagName("video")[0];
let lang = '';
let first_detected = true;
let detecting_language = false;
let urlStream = baseUrl + streamEndpoint;
let pageUrl = window.location.href;

/* Definitions for displaying subtitles */
let track = vid.addTextTrack("captions", "English", "en");
track.mode = "showing";
let MAX_LENGTH = 70;
let lorem = "Lorem ipsum dolor sit amet"

function addSubtitles(text) {
  let start = 1;
  let end = 100000;
  var prev = "";
  if (track && track.activeCues && track.activeCues.length > 0) {
    track.removeCue(track.activeCues[0]);
  }
  track.addCue(new VTTCue(start, end, prev + text));
}

/* Sleep used to wait between requests
*  Can only be used inside async functions
*/
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function sendPostRequest(url, requestBody, callback) {
  fetch(url, {method: 'post',
        headers: {
          "Content-Type": "application/json; charset=utf-8",
        },
      body: requestBody})
  .then(
    function(response) {
      if (response.status !== 200) {
        console.log('Looks like there was a problem. Status Code: ' +
          response.status);
        return;
      }
        response.json().then(function(data) {callback(data)});
      });
}

/* Functions to set and get language from chrome storage */
function getLanguage() {
    chrome.storage.sync.get(['language'], function(result) {
          if ('language' in result) {
            lang = result.language;
          }
        });
  }

function setLanguage(lang_local) {
    lang = lang_local;
    chrome.storage.sync.set({'language': lang}, function() {
      console.log("Value set to " + lang);
      chrome.storage.sync.get(['language'], function(result) {
              lang = result.language;
              console.log('Got value from callback: ' + result.language);
          });
    });
  }

  function getLanguageFromSelector() {
    getLanguage();
    if (lang === undefined) {
      setLanguage('');
    }
    getLanguage();
  }

/* Runs only once the first stream response is received. */
let firstStreamCallback = function(data) {
    if (data.subtitle == "none") {
      vid.play();
      capture();
    } else {
      subtitle = data.subtitle;
      lang = data.lang;
      vid.play();
      console.log(data.subtitle);
      console.log(data.lang);
      lang = data.lang;
      if (lang != '' && first_detected) {
        first_detected = false;
        alert('We detected the language of the video to be ' + lang + '. If this is inaccurate please adjust.');
        setLanguage(lang);
      }
      addSubtitles(data.subtitle);
      sendStreamlinkRequest();
    }
}

/* Gets called when the result of a stream request is received (but not for
the first stream request) */
let subsequentStreamRequestCallback = function(data) {
  console.log(data.subtitle);
  console.log(data.lang);
  console.log(data.video);
  if (lang != '' && first_detected) {
    first_detected = false;
    alert('We detected the language of the video to be ' + lang + '. If this is inaccurate please adjust.');
    console.log("About to set language to " + lang);
    setLanguage(lang);
  }
  addSubtitles(data.subtitle);
}

/* Send stream request */
async function sendStreamlinkRequest() {
  while (!vid.paused) {
    console.log("About to get language");
    getLanguageFromSelector();
    let request = JSON.stringify({"url": pageUrl, "lang": lang});
    sendPostRequest(urlStream, request, subsequentStreamRequestCallback);
      await sleep(3000);
  }
}

/* Gets called after response from 'subtitle' endpoint is received */
let captureCallback = function(data) {
  console.log(data.subtitle);
  console.log(data.lang);
  if (data.lang != 'detected') {
    lang = data.lang;
  }
  if (lang != '' && first_detected && lang != 'detected') {
    first_detected = false;
    alert('We detected the language of the video to be ' + lang + '. If this is inaccurate please adjust.');
    setLanguage(lang);
    vid.play();
  }
  addSubtitles(data.subtitle);
}

/* Runs when streamlink is unavailable. */
function capture() {
  let stream = vid.captureStream();
  let audioctx = new AudioContext();
  let mediaStreamNode = audioctx.createMediaStreamSource(stream);
  let numOfBufferedChunks = 0;
  let buffersSoFar = "";
  // create a script processor with input of size 16384, one input (the video) and one output (the audioctx.destination)
  let scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);
  scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {
    getLanguageFromSelector();
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
        if (!detecting_language && lang == 'detected') {
          detecting_language = true;
          lang = '';
        }
        // Send request to backend
        let jsonRrequest = {"audio": [], "sampleRate": buffersSoFar.sampleRate, "lang": lang};
        if (lang == '') {
          detecting_language = true;
          lang = 'detected';
          vid.pause();
        }
        console.log(request);
        for (let i = 0; i < buffersSoFar.getChannelData(0).length; i++) {
          jsonRequest.audio.push(buffersSoFar.getChannelData(0)[i]);
        }
        request = JSON.stringify(jsonRequest);
        let url = baseUrl + captureEndpoint
        sendPostRequest(url, request, captureCallback);
        }
      }
    };
    mediaStreamNode.connect(scriptProcessingNode);
    scriptProcessingNode.connect(audioctx.destination);
}

/* Main program that runs every time 'Translate' is clicked */
getLanguageFromSelector();
vid.pause();
console.log("Initial language passed to request " + lang);
let request = JSON.stringify({"url": pageUrl, "lang": lang});
sendPostRequest(urlStream, request, firstStreamCallback);
