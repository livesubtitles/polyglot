const localUrl = "http://127.0.0.1:8000"
const herokuUrl = "https://vast-plains-75205.herokuapp.com"
const baseUrl = herokuUrl

const languageKey = "selectedLanguage";
let languageSelector = document.getElementById('languageSelector');

function setLanguage(lang) {
<<<<<<< HEAD
  chrome.storage.sync.set({'language': lang}, function() {
    console.log("Value set to " + lang);
  });
  /*let url = "http://127.0.0.1:8000/set-language"
=======
  let url = baseUrl + "/set-language"
>>>>>>> 1cf0b5ab63005b428115d1355234b59a9682c1d3
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
