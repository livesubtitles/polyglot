const languageKey = "selectedLanguage";

function setLanguage(lang) {
  chrome.storage.sync.set({languageKey: lang}, function() {
    console.log('Value is set to ' + lang);
  });
}

let languageSelector = document.getElementById('languageSelector');
 languageSelector.onchange = () => {
  updateLanguage(languageSelector);
}
function updateLanguage(selectLanguage) {
  setLanguage(selectLanguage.value);
}

let translateButton = document.getElementById('translateButton');
 translateButton.onclick = function(elem) {
   chrome.tabs.query({active: true, currentWindow: true},
     function(tabs) {
       console.log("Clicked");
       // vid.pause();
       chrome.tabs.executeScript({file: "src/capture.js"});
  })};
