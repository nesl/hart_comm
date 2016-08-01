//var WebSocketServer = require("ws").Server;
var http = require("http");
//var fs = require('fs');
//var path = require("path");
var express = require("express");
//var readline = require('readline');

var port = 8888;

var app = express();
//app.use(express.static(__dirname+ "/../"));
//app.use('/abccccc', function(req, res, next) {
//	console.log('come to here');
//});
app.post('/x', function(req, res, next) {
	console.log('receiving post request', req);
	res.end()
});

var server = http.createServer(app);
server.listen(port, 'localhost');

console.log("http server listening on %d", port);
