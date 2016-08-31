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
fpath = args[0];
console.log('Uploading: ' + fpath);

// read hardware controller config JSON file
var config = JSON.parse(fs.readFileSync('config/config_testbench.json', 'utf8'));
var remote = config.remoteurl + ':' + config.remoteport;

// post waveform file to remote server
var req = request.post('http://' + remote + '/ctrl/waveform', function (err, resp, body) {
  if (err) {
    console.log('Error uploading waveform:');
    console.log(err);
  }
});

var form = req.form();
form.append('id', config.id);
form.append('waveform', fs.createReadStream(fpath));
