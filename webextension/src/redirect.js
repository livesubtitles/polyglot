function init() {
  lang = ''
  chrome.storage.sync.get(['language'], function(result) {
        if ('language' in result) {
          lang = result.language;
        }
        redirect(lang)
  });
}

function redirect(lang) {
  let vid = document.getElementsByTagName("video")[0];
  vid.pause();
  let reactUrl = 'https://polyglot-react.herokuapp.com/#/link=' + encodeURIComponent(window.location.href)
    + '&lang=' + lang;

   window.open(reactUrl);
}
init()
