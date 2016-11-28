import json
from klein import Klein
import subprocess
import time
import datetime
import os
import shutil

# firmware upload path
upload_root_folder_path = os.path.join('.', 'uploads')
backup_folder_path = os.path.join(upload_root_folder_path, 'backups')

required_dut_file_fields = ['dut_binary.bin']
required_input_file_fields = ['input_waveform']

class HTTPServer(object):
    app = Klein()
    config = None
    hardware = None
    dut_configs = None  # a shorthand to access dut-related configs


    def __init__(self, config):
        self.config = config
        self.dut_configs = {}
        for d in self.config["duts"]:
            self.dut_configs[ d["id"] ] = d

    def addHardware(self, hw):
        self.hardware = hw

    def start(self):
        self.app.run('0.0.0.0', self.config["localport"] )

    def burn_firmware_on_dut(self, dut_id, firmware_path, firmware_short_desp=None):
        # To make the burning process smoother, we have to copy the code to mbeds, unmound mbeds,
        # and mound mbeds. After we adapt to it, we didn't see any burning error.
        if not firmware_short_desp:
            firmware_short_desp = ''
        else:
            firmware_short_desp += ' '
        mount_path = self.dut_configs[dut_id]['mount']
        dev_path = self.dut_configs[dut_id]['dev_path']
        
        print("Removing old codes from DUT (id=%d)" % dut_id)
        subprocess.call(['rm', '-rf', '%s/*' % mount_path])
        time.sleep(3)
        
        print("programming %sfirmware on DUT %d" % (firmware_short_desp, dut_id))
        shutil.copy(firmware_path, mount_path)
        time.sleep(3)
        
        print("Unmounting.. (id=%d) %s" % (dut_id, dev_path))
        subprocess.call(['umount', dev_path])
        time.sleep(3)
        
        print("Mounting back (id=%d) %s %s" % (dut_id, dev_path, mount_path))
        subprocess.call(['mount', dev_path, mount_path])
        time.sleep(0.3)

    @app.route('/dut/program/', methods=['POST'])
    def dut_program(self, request):
        dut_files = {}
        for field in required_dut_file_fields:
            file_binary = request.args.get(field.encode())
            if not file_binary:
                print('Error: field %s is not specified' % field)
                return
            dut_files[field] = file_binary[0]

        # prepare upload folder
        if not os.path.isdir(upload_root_folder_path):
            os.makedirs(upload_root_folder_path)
        
        # create backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        backup_dir = os.path.join(backup_folder_path, 'program', now)
        os.makedirs(backup_dir)

        for field in dut_files:
            path = os.path.join(upload_root_folder_path, field)
            with open(path, 'wb') as fo:
                fo.write(dut_files[field])
            shutil.copy(path, backup_dir)
       
        #TODO: the following is time_sync homework specific
        firmware_path = os.path.join(upload_root_folder_path, 'dut_binary.bin')

        # initialize DUTs by burning do-nothing firmware
        for dut_id in [1, 2, 3]:
            self.burn_firmware_on_dut(dut_id, self.dut_configs[dut_id]['do_nothing_firmware'],
                    firmware_short_desp='blank')

        # after upload the binaries to DUT, it takes some time to refresh
        time.sleep(8.0)
        self.hardware.reset_dut()
        time.sleep(2.0)

        for dut_id in [1, 2]:
            self.burn_firmware_on_dut(dut_id, firmware_path, firmware_short_desp='student')
        
        dut_id = 3
        self.burn_firmware_on_dut(dut_id, self.dut_configs[dut_id]['real_firmware'],
                    firmware_short_desp='time sync helper')


        # after upload the binaries to DUT, it takes some time to refresh
        time.sleep(4.0)

        self.hardware.reset_dut()

        return "Firmware updated"


    # WAVEFORM UPLOAD
    @app.route('/tb/upload_input_waveform/', methods=['POST'])
    def tester_waveform(self, request):
        input_files = {}
        for field in required_input_file_fields:
            file_binary = request.args.get(field.encode())
            if not file_binary:
                print('Error: field %s is not specified' % field)
            input_files[field] = file_binary[0]
        
        # prepare upload folder
        if not os.path.isdir(upload_root_folder_path):
            os.makedirs(upload_root_folder_path)
        
        # create backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        backup_dir = os.path.join(backup_folder_path, 'input', now)
        os.makedirs(backup_dir)

        for field in input_files:
            path = os.path.join(upload_root_folder_path, field)
            with open(path, 'wb') as fo:
                fo.write(input_files[field])
            shutil.copy(path, backup_dir)

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

        request.setHeader('Content-Type', 'text/plain')
        return "DUT [%s] reset request received" % dut_id

    # HARDWARE ENGINE RESET
    @app.route('/he/reset/', methods=['POST'])
    def tester_reset(self, request):
        print('resetting tester')

        # reset tester
        self.hardware.reset_hardware_engine()

        request.setHeader('Content-Type', 'text/plain')
        return "Tester reset request received"

    # HARDWARE ENGINE START TEST
    @app.route('/tb/start/', methods=['POST'])
    def tester_start(self, request):
        print('starting test')

        waveform_path = os.path.join(upload_root_folder_path, 'input_waveform')
        
        # start testing
        self.hardware.start_test(waveform_path)

        request.setHeader('Content-Type', 'text/plain')
        return "Tester start request received"

    # GET TESTER STATUS
    @app.route('/tb/status/', methods=['GET'])
    def tester_status(self, request):
        if not self.hardware:
            return "ERROR_NOHARDWARE"
        else:
            print('Tester status requested')
            return self.hardware.get_status()

