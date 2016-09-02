import json
from klein import Klein

# firmware upload path
firmware_path = './uploads/dut_firmware.bin'
waveform_path = './uploads/waveform.txt'


class HTTPServer(object):
    app = Klein()
    config = ''

    def __init__(self, config):
        self.config = config

    def start(self):
        self.app.run('0.0.0.0', self.config["localport"])

    # DUT FIRMWARE UPDATE
    @app.route('/dut/program/', methods=['POST'])
    def dut_program(self, request):
        dut_id = int(request.args.get('dut', [-1])[0])
        dut_firmware = request.args.get('firmware', [-1])[0]
        f = open( firmware_path, 'w' )
        f.write( dut_firmware )
        f.close()
        print "programming DUT ", dut_id
        return "Firmware update for DUT [%d] received" % dut_id

    # DUT RESET
    @app.route('/dut/reset/', methods=['POST'])
    def dut_reset(self, request):
        dut_id = int(request.args.get('dut', [-1])[0])

        # reset DUT
        # TODO: !!!

        request.setHeader('Content-Type', 'text/plain')
        return "DUT [%d] reset request received" % dut_id

    # HARDWARE ENGINE RESET
    @app.route('/tester/reset/', methods=['POST'])
    def tester_reset(self, request):

        # reset tester
        # TODO: !!!

        request.setHeader('Content-Type', 'text/plain')
        return "Tester reset request received"

    # HARDWARE ENGINE START TEST
    @app.route('/tester/start/', methods=['POST'])
    def tester_start(self, request):

        # start testing
        # TODO: !!!

        request.setHeader('Content-Type', 'text/plain')
        return "Tester start request received"

    # DUT FIRMWARE UPDATE
    @app.route('/tester/waveform/', methods=['POST'])
    def tester_waveform(self, request):
        waveform = request.args.get('waveform', [-1])[0]
        f = open( waveform_path, 'w' )
        f.write( waveform )
        f.close()
        print "uploading waveform"
        return "Waveform file uploaded"

