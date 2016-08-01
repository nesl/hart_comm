//var WebSocketServer = require("ws").Server;
var http = require("http");
var express = require("express");
var bodyParser = require('body-parser');
var port = 8888;

var app = express();
app.use(bodyParser.json());


app.post('/x', function(req, res, next) {
	console.log('receiving post request', req.body.name);
	res.end()
});

var server = http.createServer(app);
server.listen(port, 'localhost');

console.log("http server listening on %d", port);
