embedButton.onclick = function(elem) {
       document.getElementById('embedButton').style.visibility = 'hidden';
       document.getElementById('embedButton').style.display = 'none';
       document.getElementById('embedText').style.visibility = 'visible';
       let languageSelector = document.getElementById('languageSelector');
       let language = languageSelector.value;
       chrome.storage.sync.set({'language': language}, function() {
         console.log("Language set");
       })
       chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
         let currentTab = tabs[0];
         let pageUrl = currentTab.url;
         console.log(pageUrl);
         let lang = "not_set";
         chrome.storage.sync.get(['language'], function(result) {
           lang = result.language;
         })
         console.log("Language is " + lang);
       });
};
