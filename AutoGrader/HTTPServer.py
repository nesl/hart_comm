import json
from klein import Klein
from subprocess import call
import time

# firmware upload path
firmware_path = './uploads/dut_firmware.bin'
waveform_path = './uploads/waveform.txt'

class HTTPServer(object):
    app = Klein()
    config = ''
    hardware = None

    def __init__(self, config):
        self.config = config

    def addHardware(self, hw):
        self.hardware = hw

    def start(self):
        self.app.run('0.0.0.0', self.config["localport"] )

    # DUT FIRMWARE UPDATE
    @app.route('/dut/program/', methods=['POST'])
    def dut_program(self, request):
        dut_id = int(request.args.get('dut', [-1])[0])
        dut_firmware = request.args.get('firmware', [-1])[0]
        f = open( firmware_path, 'w' )
        f.write( dut_firmware )
        f.close()
        print "programming DUT ", dut_id

	# get mound path for dut
	mount_path = ''
	for d in self.config["duts"]:
		if int(d["id"]) == dut_id:
			mount_path = d["mount"] 
			break

	if mount_path == '':
		print 'Error: specified DUT not found'
		return

        call(["cp", firmware_path, mount_path])
	
	# wait for it to copy and then reset the DUT
	time.sleep(2.5)
	self.hardware.reset_dut()
	time.sleep(0.20)

        return "Firmware update for DUT [%d] received" % dut_id

    # DUT RESET
    @app.route('/dut/reset/', methods=['POST'])
    def dut_reset(self, request):
        dut_id = int(request.args.get('dut', [-1])[0])
	print 'resetting DUT [%d]' % dut_id

        # reset DUT
        self.hardware.reset_dut()
	time.sleep(0.20)

        request.setHeader('Content-Type', 'text/plain')
        return "DUT [%d] reset request received" % dut_id

    # HARDWARE ENGINE RESET
    @app.route('/tester/reset/', methods=['POST'])
    def tester_reset(self, request):
	print 'resetting tester'

        # reset tester
        self.hardware.reset_tester()
	time.sleep(0.20)

        request.setHeader('Content-Type', 'text/plain')
        return "Tester reset request received"

    # HARDWARE ENGINE START TEST
    @app.route('/tester/start/', methods=['POST'])
    def tester_start(self, request):
	print 'starting test'

        # start testing
        self.hardware.start_test(waveform_path)
	time.sleep(0.20)

        request.setHeader('Content-Type', 'text/plain')
        return "Tester start request received"

    # WAVEFORM UPLOAD
    @app.route('/tester/waveform/', methods=['POST'])
    def tester_waveform(self, request):
        waveform = request.args.get('waveform', [-1])[0]
        f = open( waveform_path, 'w' )
        f.write( waveform )
        f.close()
        print "uploading waveform"
        return "Waveform file uploaded"

    # GET TESTER STATUS
    @app.route('/tester/status/', methods=['GET'])
    def tester_status(self, request):
        if self.hardware is None:
            return "ERROR_NOHARDWARE"
        else:
            print 'Tester status requested'
            return self.hardware.get_status()

