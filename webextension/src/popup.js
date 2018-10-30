let translateButton = document.getElementById('translateButton');
 translateButton.onclick = function(elem) {
   chrome.tabs.query({active: true, currentWindow: true},
     function(tabs) {
       console.log("Clicked");
       // vid.pause();
       chrome.tabs.executeScript({file: "src/capture.js"});
  })};
