const io = require('socket.io-client');
const sock = io("http://127.0.0.1:5000/");
sock.on('connection', function(res){
  console.log('Connected');
  console.log("Received: " + res);
  console.log(res);
});
