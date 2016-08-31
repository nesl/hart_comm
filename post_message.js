/*
 * POST MEASURED WAVEFORM FILE
*/

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

// ===== PARSE COMMANDLINE ARGS =====
var args = process.argv.slice(2);
message = args[0];

// read hardware controller config JSON file
var config = JSON.parse(fs.readFileSync('config/config_testbench.json', 'utf8'));
var remote = config.remoteurl + ':' + config.remoteport;

// post status
request(
	{
		uri: "http://" + remote + "/tb/msg",
		method: "POST",
		form: {
			id: config.id,
			msg: message
		}
	}, function(error, response, body) {
		// do nothing with server error or response
	}
);

