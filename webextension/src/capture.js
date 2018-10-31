let vid = document.getElementsByTagName("video")[0];
let track = vid.addTextTrack("captions", "English", "en");
let lang = '';
let first_detected = true;
let detecting_language = false;
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

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function sendStreamlinkRequest() {
  urlStream = "http://127.0.0.1:8000/stream-subtitle"
  while (!vid.paused) {
    let request = JSON.stringify(JSON.parse("{\"url\":\"" + pageUrl + "\", \"lang\":\"" + lang + "\"}"));
    fetch(urlStream, {method: 'post',
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
          console.log(data.lang);
          if (data.lang != 'detected') {
            lang = data.lang;
          }
          if (lang != '' && first_detected) {
            first_detected = false;
            alert('We detected the language of the video to be ' + lang + '. If this is inaccurate please adjust.');
          }
          addSubtitles(data.subtitle);
        });
      });
      await sleep(3000);
  }
}

let urlStream = "http://127.0.0.1:8000/stream"
let pageUrl = window.location.href;
vid.pause();
let request = JSON.stringify(JSON.parse("{\"url\":\"" + pageUrl + "\", \"lang\":\"" + lang + "\"}"));
fetch(urlStream, {method: 'post',
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
        if (data.subtitle == "none") {
          vid.play();
          capture();
        } else {
        subtitle = data.subtitle;
        lang = data.lang;
        vid.play();
        console.log(data.subtitle);
        console.log(data.lang);
        if (data.lang != 'detected') {
          lang = data.lang;
        }
        if (lang != '' && first_detected) {
          first_detected = false;
          alert('We detected the language of the video to be ' + lang + '. If this is inaccurate please adjust.');
        }
        addSubtitles(data.subtitle);
        sendStreamlinkRequest();
      }
      });
  });

const languageKey = "selectedLanguage";

function getLanguage() {
  let language = '';
  chrome.storage.sync.get([languageKey], function(result) {
    console.log(result);
    console.log('Value currently is ' + result.languageKey);
    language = result.languageKey;
  });
  return language;
}

function setLanguage(lang) {
  console.log('Setting language' + lang);
  chrome.storage.sync.set({languageKey: lang}, function() {
    console.log('Value is set to ' + lang);
  });
}

function capture() {
  let stream = vid.captureStream();
  let audioctx = new AudioContext();
  let mediaStreamNode = audioctx.createMediaStreamSource(stream);
  let numOfBufferedChunks = 0;
  let buffersSoFar = "";
  // create a script processor with input of size 16384, one input (the video) and one output (the audioctx.destination)
  let scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);
  scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {
    // ----


    if (getLanguage("selectedLanguage") === null) {
      setLanguage('');
    }
    lang = getLanguage("selectedLanguage");
    // ----
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
        let request = "{\"audio\":" + "[]" + ", \"sampleRate\": " + buffersSoFar.sampleRate + ", \"lang\":\"" + lang + "\"}";
        if (lang == '') {
          detecting_language = true;
          lang = 'detected';
          vid.pause();
        }
        console.log(request);
        let jsonRequest = JSON.parse(request);
        for (let i = 0; i < buffersSoFar.getChannelData(0).length; i++) {
          jsonRequest.audio.push(buffersSoFar.getChannelData(0)[i]);
        }
        request = JSON.stringify(jsonRequest);
        let url = "http://127.0.0.1:8000/subtitle"
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
              console.log(data.lang);
              if (data.lang != 'detected') {
                lang = data.lang;
              }
              if (lang != '' && first_detected && lang != 'detected') {
                first_detected = false;
                alert('We detected the language of the video to be ' + lang + '. If this is inaccurate please adjust.');
                // ---
              	setLanguage(data.lang);
		// ---

                vid.play();
              }
              addSubtitles(data.subtitle);
            });
          });

        }
      }
    };
    mediaStreamNode.connect(scriptProcessingNode);
    scriptProcessingNode.connect(audioctx.destination);
}
