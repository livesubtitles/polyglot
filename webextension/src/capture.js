/* Url definitions */
const localUrl = "http://127.0.0.1:8000";
const herokuUrl = "https://polyglot-livesubtitles.herokuapp.com";
const baseUrl = herokuUrl;
const captureEndpoint = "/subtitle";
const streamEndpoint = "/stream";
const punctuateEndpoint = "http://flask-env.p5puf6mmb3.eu-west-2.elasticbeanstalk.com/punctuate";

/* Definitions for capture and stream requests */
var vid = document.getElementsByTagName("video")[0];
var lang = '';
var first_detected = true;
var detecting_language = false;
var urlStream = baseUrl + streamEndpoint;
var pageUrl = window.location.href;

/* Definitions for displaying subtitles */
var track = vid.addTextTrack("captions", "English", "en");
track.mode = "showing";
var MAX_LENGTH = 70;
var lorem = "Lorem ipsum dolor sit amet"

function addSubtitles(text) {
  var start = 1;
  var end = 100000;
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
            if (lang != '') {
              first_detected = false;
            }
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
// var firstStreamCallback = function(data) {
//     if (data.subtitle == "none") {
//       vid.play();
//       capture();
//     }
// }

/* Send stream request */
async function sendStreamlinkRequest() {
    console.log("About to get language");
    getLanguageFromSelector();
    var request = JSON.stringify({"url": pageUrl, "lang": lang});
    sendPostRequest(urlStream, request, subsequentStreamRequestCallback);
    await sleep(3000);
}

/* Gets called after response from 'subtitle' endpoint is received */
var captureCallback = function(data) {
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
  var stream = vid.captureStream();
  var audioctx = new AudioContext();
  var mediaStreamNode = audioctx.createMediaStreamSource(stream);
  var numOfBufferedChunks = 0;
  var buffersSoFar = "";
  // create a script processor with input of size 16384, one input (the video) and one output (the audioctx.destination)
  var scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);
  scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {
    getLanguageFromSelector();
    if (!vid.paused) {
      if (numOfBufferedChunks == 0) {
        buffersSoFar = audioProcessingEvent.inputBuffer;
      } else {
        // merge the previous buffers with the new one
        var mergedBuffer = audioctx.createBuffer(1, buffersSoFar.length + audioProcessingEvent.inputBuffer.length, audioProcessingEvent.inputBuffer.sampleRate);
        var channel = mergedBuffer.getChannelData(0);
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
        var jsonRequest = {"audio": [], "sampleRate": buffersSoFar.sampleRate, "lang": lang};
        if (lang == '') {
          detecting_language = true;
          lang = 'detected';
          vid.pause();
        }
        console.log(jsonRequest);
        for (var i = 0; i < buffersSoFar.getChannelData(0).length; i++) {
          jsonRequest.audio.push(buffersSoFar.getChannelData(0)[i]);
        }
        request = JSON.stringify(jsonRequest);
        var url = baseUrl + captureEndpoint
        sendPostRequest(url, request, captureCallback);
        }
      }
    };
    mediaStreamNode.connect(scriptProcessingNode);
    scriptProcessingNode.connect(audioctx.destination);
}

/* Main program that runs every time 'Translate' is clicked */
getLanguageFromSelector();
capture();
// vid.pause();
// console.log("Initial language passed to request " + lang);
// var request = JSON.stringify({"url": pageUrl, "lang": lang});
// sendPostRequest(urlStream, request, firstStreamCallback);
