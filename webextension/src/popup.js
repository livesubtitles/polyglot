const localUrl = "http://127.0.0.1:8000"
const herokuUrl = "https://polyglot-livesubtitles.herokuapp.com"
const baseUrl = herokuUrl

const languageKey = "selectedLanguage";
let languageSelector = document.getElementById('languageSelector');

function setLanguage(lang) {
  chrome.storage.sync.set({'language': lang}, function() {
    console.log("Value set to " + lang);
  });
}

languageSelector.onchange = () => {
  updateLanguage(languageSelector);
}

function updateLanguage(selectLanguage) {
  setLanguage(selectLanguage.value);
}

var url, tab;
function init(){
  chrome.storage.sync.set({'language': ''}, function() {
        chrome.tabs.query({currentWindow: true, active: true},function(tabs){
           url = tabs[0].url;
           tab = tabs[0];

           flag = fetch(herokuUrl + '/supports?web=' + url)
                   .then(resp => resp.json());
           //Now that we have the data we can proceed and do something with it
           flag.then(function(result) {
              processTab(url, result.answer);
           })
      })
    });
  }

init();
function processTab(url, flag) {
  let clicked = false;
  let translateButton = document.getElementById('translateButton');
   translateButton.onclick = function(elem) {
     chrome.tabs.query({active: true, currentWindow: true},
       function(tabs) {
         if (!clicked) {
           let streamlinkSupportsIt = flag;
           if (streamlinkSupportsIt /*&& false /*disables streamlink*/) {
             chrome.tabs.executeScript({file: "src/redirect.js"});
           } else {
             console.log("Clicked");
             clicked = true;
             console.log("Calling set language from popup.js with lang = " + languageSelector.value);
             setLanguage(languageSelector.value);
             chrome.tabs.executeScript({file: "src/capture.js"});
           }
         } else {
           console.log("Calling set language from popup.js with lang = " + languageSelector.value);
           setLanguage(languageSelector.value);
         }
  })};
}
