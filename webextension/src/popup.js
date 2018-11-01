const localUrl = "http://127.0.0.1:8000"
const herokuUrl = "https://vast-plains-75205.herokuapp.com"
const baseUrl = herokuUrl

const languageKey = "selectedLanguage";
let languageSelector = document.getElementById('languageSelector');

function setLanguage(lang) {
  let url = baseUrl + "/set-language"
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
    });
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
         setLanguage(languageSelector.value);
         chrome.tabs.executeScript({file: "src/capture.js"});
       } else {
         setLanguage(languageSelector.value);
       }
       // vid.pause();
  })};
