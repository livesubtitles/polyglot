import updateSelectedLanguage from './capture.js';

function updateLanguage(selectLanguage) {
  localStorage.setItem("selectedLanguage", selectLanguage.value);
  updateSelectedLanguage();
}

let translateButton = document.getElementById('translateButton');
 translateButton.onclick = function(elem) {
   chrome.tabs.query({active: true, currentWindow: true},
     function(tabs) {
      chrome.tabs.executeScript({file: "src/capture.js"});
    })
  };
