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

var url, tab;
function init(){
    chrome.tabs.query({currentWindow: true, active: true},function(tabs){
       url = tabs[0].url;
       tab = tabs[0];
       //Now that we have the data we can proceed and do something with it
       processTab();
    });
}

function processTab(){
    // Use url & tab as you like
    console.log(url);
    console.log(tab);
}

function geatUrl() {
  let x = "";
  console.log("Extension starts here");

  chrome.tabs.getSelected(null, function(tab) {
    myFunction(tab.url);
    x = tab.url
  });
  return x;
}

function myFunction(tablink) {
  // do stuff here
  console.log(tablink);
}

  // x = chrome.tabs.query({'active': true, 'lastFocusedWindow': true}, function (tabs) {
  //   var url = tabs[0].url;
  //   console.log(url);
  //   return url;
    // x = url;
  // });
  // chrome.tabs.getSelected(null,function(tab) {
  //   console.log(tab.url);
  //   x = tab.url;
  // });
//   console.log("x is " + x);
//   return x;
// }
init()
function processTab() {
  let clicked = false;
  let translateButton = document.getElementById('translateButton');
   translateButton.onclick = function(elem) {
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

             let reactUrl = 'https://www.polyglot-react.herokuapp.com/#/link=' + encodeURIComponent(url)
              + '&lang=en-US';
            // let reactUrl = 'https://www.google.com'
             window.open(reactUrl);
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
         // vid.pause();
  })};
}
