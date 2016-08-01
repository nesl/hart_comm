//var WebSocketServer = require("ws").Server;
var http = require("http");
//var fs = require('fs');
//var path = require("path");
var express = require("express");
//var readline = require('readline');
var request = require("request");

var port = 8889;

var app = express();
//app.use(express.static(__dirname+ "/../"));
//app.use('/abccccc', function(req, res, next) {
//	console.log('come to here');
//});

var foreign_url = "localhost:8888";

app.post('/y', function(req, res, next) {
	request({
		uri: "http://" + foreign_url + "/x",
		method: "POST",
		form: {
			name: "Bob"
		}
	}, function(error, response, body) {
		  console.log(body);
	});
	console.log('receiving post request');
	res.end()
});

console.log("app listening on %d ", port);

var server = http.createServer(app);
server.listen(port, 'localhost');

console.log("http server listening on %d", port);
