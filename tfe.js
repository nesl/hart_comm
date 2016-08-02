// ===== REQUIRED PACKAGES =====
var http = require("http");
var express = require("express");
var request = require("request");
var bodyParser = require('body-parser');
var querystring = require('querystring');
var fs = require('fs');

// ===== LOCAL LIBRARIES =====
var dutlib = require('./jsobjects/dut.js');
var testbenchlib = require('./jsobjects/testbench.js');

// read config file
var config = JSON.parse(fs.readFileSync('config/config_testbench.json', 'utf8'));
var remote = config.remoteurl + ':' + config.remoteport;

// configure Testbench
var ANNOUNCE_PERIOD = 10*1000;
console.log('Initializing testbench Type: [' + config.type + '], Id: [' + config.id + ']' );
var testbench = new testbenchlib.Testbench(config.type, config.id, config.localport);
numDuts = config.duts.length;
for( var i=0; i<numDuts; i++ ){
	d = config.duts[i];
	dut = new dutlib.Dut(d.type, d.id, d.path);
	console.log('     ...adding DUT [' + d.name + '] at ' + dut.path);
	testbench.addDut( dut );
}

// creating the express app
var app = express();
app.use(bodyParser.json());

// DUT Firmware Programming
app.post('/dut_program', function(req, res, next) {
	var target = req.body.dut;
	var firmware = req.body.firmware;
	console.log('Firmware received for ', target.name);
	// TODO: Program specified target
});

// DUT Reset
app.post('/dut_reset', function(req, res, next) {
	var target = req.body.dut;
	console.log('Reset requested for ', target.name);
	// TODO: Reset specified target
});

// Fire up the server
var server = http.createServer(app);
server.listen(config.localport, 'localhost');
console.log("http server listening on %d", config.localport);

// Announce test bench to the server every 10 seconds
function announcePresence() {
	// determine connected devices
	console.log("announcing presence to server...");
	request({
		uri: "http://" + remote + "/testbench",
		method: "POST",
		form: {
			testbench: JSON.stringify(config)
		}
	}, function(error, response, body) {
		  console.log(body);
	});
	setTimeout(announcePresence, ANNOUNCE_PERIOD);
}
setTimeout(announcePresence, ANNOUNCE_PERIOD);
