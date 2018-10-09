// On extension install
chrome.runtime.onInstalled.addListener(function() {
  console.log("Polyglot installed successfully!");

  // only show the extension as clickable if the webpage has a video in it.
  // note that if the video has display: none or visibility: hidden, the rule
  // won't match
  chrome.declarativeContent.onPageChanged.removeRules(undefined, function() {
      chrome.declarativeContent.onPageChanged.addRules([{
        conditions: [
          new chrome.declarativeContent.PageStateMatcher({
            css: ["video"]
          })
        ],
            actions: [new chrome.declarativeContent.ShowPageAction()]
      }]);
    });
});
