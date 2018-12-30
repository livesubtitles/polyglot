let vid = document.getElementsByTagName("video")[0];
vid.pause()
let reactUrl = 'http://polyglot-react.herokuapp.com/#/link=' + encodeURIComponent(window.location.href)
  + '&lang=es-ES';
// let reactUrl = 'https://www.google.com'
 window.open(reactUrl);
