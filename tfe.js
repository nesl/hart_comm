var http = require("http");
var express = require("express");
var request = require("request");
var bodyParser = require('body-parser');
var querystring = require('querystring');

// local IP information
var port = 8889;

// remote IP information
var server_url = "localhost:8888";

// creating the express app
var app = express();
app.use(bodyParser.json());

app.post('/y', function(req, res, next) {
	var form = {
		name: "Bob"
	};
	var formData = querystring.stringify(form);
	var contentLength = formData.length;

	request({
		headers: {
			'Content-Length': contentLength,
			'Content-Type': 'application/x-www-form-urlencoded'
		},
		uri: "http://" + server_url + "/x",
		body: formData,
		method: "POST",
	}, function(error, response, body) {
		  console.log(body);
	});
	console.log('receiving post request');
	res.end()
});

// Fire up the server
console.log("app listening on %d ", port);
var server = http.createServer(app);
server.listen(port, 'localhost');
console.log("http server listening on %d", port);
