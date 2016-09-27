import json
from klein import Klein
from subprocess import call
import time
import datetime
import os
import shutil

# firmware upload path
upload_root_folder_path = os.path.join('.', 'uploads')
backup_folder_path = os.path.join(upload_root_folder_path, 'backups')
waveform_path = os.path.join(upload_root_folder_path, 'waveform.txt')


class HTTPServer(object):
    app = Klein()
    config = None
    hardware = None
    dut_configs = None  # a shorthand to access dut-related configs


    def __init__(self, config):
        self.config = config
        self.dut_configs = {}
        for d in self.config["duts"]:
            self.dut_configs[ d["id"] ] = d:

    def addHardware(self, hw):
        self.hardware = hw

    def start(self):
        self.app.run('0.0.0.0', self.config["localport"] )

    # DUT FIRMWARE UPDATE
    @app.route('/dut/program/', methods=['POST'])
    def dut_program(self, request):
        num_duts_list = request.args.get('num_duts'.encode())
        if not num_duts:
            print('Error: num_duts field is not specified')
            return
        try:
            num_duts = int(dut_ids[0].decode())
        except:
            print('Error: incorrect format in num_duts field')
            return

        dut_id_2_firmware = {}
        for i in range(num_duts):
            key = 'dut%d' % i
            dut_ids = request.args.get(key.encode())
            if not dut_ids:
                print('Error: %s field is not specified' % key)
                return
            dut_id = dut_ids[0]
            if not self.dut_configs[dut_id]:
                print('Error: specified DUT (id=%s) not found', dut_id)
                return
            
            key = 'firmware%d' % i
            dut_firmware_list = request.args.get(key.encode())
            if not dut_firmware_list:
                print('Error: %s field is not specified' % key)
                return
            dut_firmware = dut_firmware_list[0]

            dut_id_2_firmware[dut_id] = dut_firmware

        if len(dut_id_2_firmware) != len(self.dut_configs):
            print('Error: not all DUT firmwares are specified')
            return

        if not os.path.isdir(upload_root_folder_path):
            os.makedirs(upload_root_folder_path)
        
        # create backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        backup_dir = os.path.join(backup_folder_path, 'program', now)
        os.makedirs(backup_dir)

        for dut_id in dur_id_2_firmware:
            firmware_path = os.path.join(upload_root_folder_path, 'dut%s_firmware.bin' % dut_id)
            with open( firmware_path, 'wb' ) as f:
                f.write( dut_firmware )
            shutil.copy(firmware_path, backup_dir)
            shutil.copyfile(firmware_path, mount_path)
            print("programming DUT %s" % dut_id)


        # wait for it to copy and then reset the DUT
		#TODO: check why do we need these delay
        time.sleep(2.5)
        self.hardware.reset_dut()
        time.sleep(0.20)

        return "Firmware updated"


    # WAVEFORM UPLOAD
    @app.route('/tester/waveform/', methods=['POST'])
    def tester_waveform(self, request):
        waveform_list = request.args.get('waveform'.encode())
        if not waveform_list:
            print('Error: waveform field is not specified')
            return
        waveform = waveform_list[0]
        with open( waveform_path, 'wb' ) as f:
            f.write( waveform )

        # backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        backup_dir = os.path.join(backup_folder_path, 'waveform', now)
        os.makedirs(backup_dir)
        shutil.copy(waveform_path, backup_dir)

        print("uploading waveform")
        return "Waveform file uploaded"


    # DUT RESET
    @app.route('/dut/reset/', methods=['POST'])
    def dut_reset(self, request):
        dut_ids = request.args.get('dut'.encode())
        if not dut_ids:
            print('Error: dut field is not specified')
            return
        try:
            dut_id = dut_ids[0].decode()
        except:
            print('Error: incorrect format in dut field')
            return

        # reset DUT
        self.hardware.reset_dut()
        time.sleep(0.20)

        request.setHeader('Content-Type', 'text/plain')
        return "DUT [%s] reset request received" % dut_id

    # HARDWARE ENGINE RESET
    @app.route('/tester/reset/', methods=['POST'])
    def tester_reset(self, request):
        print('resetting tester')

        # reset tester
        self.hardware.reset_tester()
        time.sleep(0.20)

        request.setHeader('Content-Type', 'text/plain')
        return "Tester reset request received"

    # HARDWARE ENGINE START TEST
    @app.route('/tester/start/', methods=['POST'])
    def tester_start(self, request):
        print('starting test')

        # start testing
        self.hardware.start_test(waveform_path)
        time.sleep(0.20)

        request.setHeader('Content-Type', 'text/plain')
        return "Tester start request received"

    # GET TESTER STATUS
    @app.route('/tester/status/', methods=['GET'])
    def tester_status(self, request):
        if not self.hardware:
            return "ERROR_NOHARDWARE"
        else:
            print('Tester status requested')
            return self.hardware.get_status()

