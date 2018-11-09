(function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
const video = document.getElementById('video');
console.log(video);

console.log("Hello");
var hls = new Hls();
hls.loadSource('https://localhost:8000/temp/temp.ts');
console.log("HELLO");
hls.attachMedia(video);
hls.on(Hls.Events.MANIFEST_PARSED, function() {
		video.play();
});	


// ---- Socket stuff ---- //
// const io = require('socket.io-client');
// const socket = io('http://localhost:8000/stream')

// socket.on('connect', function() {
//     console.log("Socket connected");
//     socket.emit('stream', {url: "https://www.youtube.com/watch?v=mV8jp1N2fSw", lang: "es-ES"})
// });

// socket.on('stream-response', function(data) {
// 	console.log("Recieved stream-response");
// 	var json = JSON.parse(data);
	
// });
},{}]},{},[1]);
