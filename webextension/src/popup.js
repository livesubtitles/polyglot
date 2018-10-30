
let languageSelector = document.getElementById('languageSelector');

languageSelector.onchange = () => {
  updateLanguage(languageSelector);
}
function updateLanguage(selectLanguage) {
  localStorage.setItem("selectedLanguage", selectLanguage.value);
}

let translateButton = document.getElementById('translateButton');
 translateButton.onclick = function(elem) {
   chrome.tabs.query({active: true, currentWindow: true},
     function(tabs) {
      chrome.tabs.executeScript({file: "src/capture.js"});
    })
  };
