const { series, src, dest } = require('gulp');

function moveHtml() {
  return src("webextension/src/*.html").pipe(dest("build/src"));
}

function moveManifest() {
  return src("webextension/manifest.json").pipe(dest("build/"));
}

function moveImages() {
  return src("webextension/icon*.*").pipe(dest("build/"));
}

exports.default = series(moveHtml, moveManifest, moveImages);
