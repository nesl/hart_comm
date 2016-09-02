/*
 * TESTBENCH FRONT END (tfe)
*/

// ===== REQUIRED PACKAGES =====
var http = require("http");
var express = require("express");
var request = require("request");
var bodyParser = require('body-parser');
var querystring = require('querystring');
var fs = require('fs');
var multer = require('multer');
const execSync = require('child_process').execSync;

// ===== LOCAL LIBRARIES =====
var dutlib = require('./jsobjects/dut.js');
var testbenchlib = require('./jsobjects/testbench.js');

// ===== READ CONFIG FILE =====
var args = process.argv.slice(2);
configFile = args[0];
var config = JSON.parse(fs.readFileSync(configFile, 'utf8'));
var remote = config.remoteurl + ':' + config.remoteport;

// ===== FIRMWARE STORAGE =====
var firmware_storage = multer.diskStorage({
	destination: './uploads/',
	limits: { fileSize: 10*Math.pow(2,20) },
	filename: function (req, file, cb) {
        cb(null, 'dut_firmware.bin')
  	}
});
var upload_firmware = multer({ storage: firmware_storage })

// ===== WAVEFORM STORAGE =====
var waveform_storage = multer.diskStorage({
	destination: './uploads/',
	limits: { fileSize: 10*Math.pow(2,20) },
	filename: function (req, file, cb) {
        cb(null, 'dut_waveform.wvf')
  	}
});
var upload_waveform = multer({ storage: waveform_storage })



// configure Testbench for periodic advertisements using config file
var ANNOUNCE_PERIOD = 10*1000;
console.log('Initializing testbench Type: [' + config.type + '], Id: [' + config.id + ']' );
var testbench = new testbenchlib.Testbench(config.type, config.id, config.localport);
numDuts = config.duts.length;
for( var i=0; i<numDuts; i++ ){
	d = config.duts[i];
	dut = new dutlib.Dut(d.type, d.id, d.mount);
	console.log('     ...adding DUT [' + d.name + '] at ' + dut.path);
	testbench.addDut( dut );
}

// creating the node.js express app
var app = express();
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended:false }));

// =============== HTTP PROTOCOL HOOKS ===============
// DUT Firmware Programming
app.post('/dut/program', upload_firmware.single('firmware'), function(req, res, next) {
	var target = req.body.dut;
	console.log('Firmware uploading for DUT: ', target);

	// find path for specified DUT id
	path = ''
	for( var i=0; i<numDuts; i++){
		d = config.duts[i];
		if( d.id == target ){
			path = config.duts[i].mount;
			break;
		}
	}

	if( path == '' ){
		// DUT not found
		res.end('No such DUT found');
		return;
	}

	// Copy firmware to DUT
	sysResult = execSync('cp ./uploads/dut_firmware.bin ' + path);

	res.end()
});

// DUT Reset
app.post('/dut/reset', function(req, res, next) {
	var target = req.body.dut;
	console.log('Reset requested for DUT #', target);

	// TODO: Reset specified target
	// !!!

	res.end()
});

// TESTER ENGINE Reset
app.post('/tester/reset', function(req, res, next) {
	console.log('Reset requested for test engine');

	// TODO: Reset specified target
	// !!!

	res.end()
});

// TESTER ENGINE begin test
app.post('/tester/start', function(req, res, next) {
	console.log('Start requested for test engine');

	// Reset specified target

	res.end()
});

// CONTROLLER upload test waveform file
app.post('/ctrl/waveform', upload_waveform.single('waveform'), function(req, res, next) {
	var target = req.body.dut;
	console.log('Waveform uploading for DUT: ', target);

	// TODO: Reset specified target
	// !!!

	res.end()
});

// =============== ANNOUNCE TESTBED TO SERVER ===============
function announcePresence() {
	// determine connected devices
	//console.log("announcing testbed to server...");
	request({
		uri: "http://" + remote + "/tb/summary/",
		method: "POST",
		form: {
			testbench: JSON.stringify(config)
		}
	}, function(error, response, body) {
		// do nothing with server error or response
	});
	setTimeout(announcePresence, ANNOUNCE_PERIOD);
}
setTimeout(announcePresence, ANNOUNCE_PERIOD);

// =============== FIRE UP THE SERVER ===============
var server = http.createServer(app);
server.listen(config.localport);
console.log("HTTP server listening on %d", config.localport);
