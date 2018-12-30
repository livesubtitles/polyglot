const localUrl = "http://127.0.0.1:8000"
const herokuUrl = "https://polyglot-livesubtitles.herokuapp.com"
const baseUrl = herokuUrl

const languageKey = "selectedLanguage";
let languageSelector = document.getElementById('languageSelector');
var lang = '';

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

function getLanguage() {
    chrome.storage.sync.get(['language'], function(result) {
          if ('language' in result) {
            languageSelector.value = result.language;
            setLanguage(languageSelector.value);
          }
        });
  }

var url, tab;
function init(){
  chrome.storage.sync.set({'language': languageSelector.value}, function() {
    chrome.tabs.query({currentWindow: true, active: true},function(tabs){
       url = tabs[0].url;
       tab = tabs[0];
       //Now that we have the data we can proceed and do something with it
       processTab();
    });
  })
}

getLanguage();
init()
function processTab() {
  let clicked = false;
  let translateButton = document.getElementById('translateButton');
   translateButton.onclick = function(elem) {
     translateButton.style.display = "none";
     chrome.tabs.query({active: true, currentWindow: true},
       function(tabs) {
         if (!clicked) {
           let streamlinkSupportsIt = false;
            const request = async () => {
              const response = await fetch(herokuUrl + '/supports?web=' + url);
              const json = await response.json();
              console.log(json);
              return json;
            }

            streamlinkSupportsIt = request().then(function(result) {
                return result;
            });
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
