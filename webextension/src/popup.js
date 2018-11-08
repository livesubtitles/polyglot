const localUrl = "http://127.0.0.1:8000"
const herokuUrl = "https://polyglot-livesubtitles.herokuapp.com"
const baseUrl = herokuUrl

const languageKey = "selectedLanguage";
let languageSelector = document.getElementById('languageSelector');

function setLanguage(lang) {
  chrome.storage.sync.set({'language': lang}, function() {
    console.log("Value set to " + lang);
  });
  /*let url = "http://127.0.0.1:8000/set-language"
  fetch(url, {method: 'post',
        headers: {
          "Content-Type": "application/json; charset=utf-8",
        },
      body: lang})
  .then(
    function(response) {
      if (response.status !== 200) {
        console.log('Looks like there was a problem. Status Code: ' +
          response.status);
        return;
      }
    });*/
}

 languageSelector.onchange = () => {
  updateLanguage(languageSelector);
}
function updateLanguage(selectLanguage) {
  setLanguage(selectLanguage.value);
}

let clicked = false;
let translateButton = document.getElementById('translateButton');
 translateButton.onclick = function(elem) {
   chrome.tabs.query({active: true, currentWindow: true},
     function(tabs) {
       if (!clicked) {
         console.log("Clicked");
         clicked = true;
         console.log("Calling set language from popup.js with lang = " + languageSelector.value);
         setLanguage(languageSelector.value);
         chrome.tabs.executeScript({file: "src/capture.js"});
       } else {
         console.log("Calling set language from popup.js with lang = " + languageSelector.value);
         setLanguage(languageSelector.value);
       }
       // vid.pause();
  })};
