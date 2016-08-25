/*
 * SERVER BACK END (sbe)
*/

// ===== REQUIRED PACKAGES =====
var http = require("http");
var express = require("express");
var bodyParser = require('body-parser');
var port = 8888;

// creating the node.js express app
var app = express();
app.use(bodyParser.urlencoded({ extended:false }));


// =============== HTTP PROTOCOL HOOKS ===============
// for testbench advertisements
app.post('/testbench', function(req, res, next) {
	console.log('testbench announcement:', req.body.testbench );
	res.end()
});

// =============== FIRE UP THE SERVER ===============
var server = http.createServer(app);
server.listen(port, 'localhost');
console.log("HTTP server listening on %d", port);
