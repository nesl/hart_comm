function Testbench(type, id, port) {
    this.type = type;
    this.id = id;
    this.port = port;
    this.duts = [];
    this.addDut = function (dut) {
        this.duts.push(dut);
    };
}

module.exports.Testbench = Testbench;