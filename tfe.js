var http = require("http");
var express = require("express");
var request = require("request");
var bodyParser = require('body-parser');


// local IP information
var port = 8889;

// remote IP information
var server_url = "localhost:8888";

// misc. variables
var ANNOUNCE_PERIOD = 1*1000;
var testbench_id = 11;
var dut_list = 0;

// creating the express app
var app = express();
app.use(bodyParser.json());

app.post('/y', function(req, res, next) {
	request({
		uri: "http://" + server_url + "/x",
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

// Fire up the server
console.log("app listening on %d ", port);
var server = http.createServer(app);
server.listen(port, 'localhost');
console.log("http server listening on %d", port);

// Announce test bench to the server every 10 seconds
function announcePresence() {
  console.log("announcing presence to server...");
  request({
		uri: "http://" + server_url + "/testbench",
		method: "POST",
		form: {
			id: testbench_id,
			duts: dut_list,
		}
	}, function(error, response, body) {
		  console.log(body);
	});
  setTimeout(announcePresence, ANNOUNCE_PERIOD);
}
setTimeout(announcePresence, ANNOUNCE_PERIOD);
