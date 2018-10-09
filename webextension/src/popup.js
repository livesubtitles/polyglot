let translateButton = document.getElementById('translateButton');
 translateButton.onclick = function(elem) {
   chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.executeScript(
          {code: "let vid = document.getElementsByTagName('video')[0];let stream = vid.captureStream();let audioctx = new AudioContext();let mediaStreamNode = audioctx.createMediaStreamSource(stream);let scriptProcessingNode = audioctx.createScriptProcessor(16384, 1, 1);scriptProcessingNode.onaudioprocess = function(audioProcessingEvent) {console.log(audioProcessingEvent);};mediaStreamNode.connect(scriptProcessingNode);scriptProcessingNode.connect(audioctx.destination);"});
    });
 };
