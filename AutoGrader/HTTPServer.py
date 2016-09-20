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
firmware_path = os.path.join(upload_root_folder_path, 'dut_firmware.bin')
waveform_path = os.path.join(upload_root_folder_path, 'waveform.txt')


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
        #TODO: in the future, we should consider uploading several dut firmwares at the same time.
        #      try to have 'num_duts' field, then 'dut0_firmware', dut1_firmware', etc
        dut_ids = request.args.get('dut'.encode())
        if not dut_ids:
            print('Error: dut field is not specified')
            return
        try:
            dut_id = dut_ids[0].decode()
        except:
            print('Error: incorrect format in dut field')
            return

        dut_firmware_list = request.args.get('firmware'.encode())
        if not dut_firmware_list:
            print('Error: firmware field is not specified')
            return
        dut_firmware = dut_firmware_list[0]

        if not os.path.isdir(upload_root_folder_path):
            os.makedirs(upload_root_folder_path)
        with open( firmware_path, 'wb' ) as f:
            f.write( dut_firmware )
        print("programming DUT %s" % dut_id)

        # get mound path for dut
        mount_path = ''
        for d in self.config["duts"]:
            if d["id"] == dut_id:
                mount_path = d["mount"] 
                break

        if mount_path == '':
            print('Error: specified DUT not found')
            return

        # backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        backup_dir = os.path.join(backup_folder_path, 'program', now)
        os.makedirs(backup_dir)
        shutil.copy(firmware_path, backup_dir)
        with open(os.path.join(backup_dir, 'dut'), 'w') as f:
            f.write(dut_id)

        shutil.copyfile(firmware_path, mount_path)

        # wait for it to copy and then reset the DUT
        time.sleep(2.5)
        self.hardware.reset_dut()
        time.sleep(0.20)

        return "Firmware update for DUT [%d] received" % dut_id

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

    # GET TESTER STATUS
    @app.route('/tester/status/', methods=['GET'])
    def tester_status(self, request):
        if not self.hardware:
            return "ERROR_NOHARDWARE"
        else:
            print('Tester status requested')
            return self.hardware.get_status()

