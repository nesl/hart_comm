import json
from klein import Klein
import time
import datetime
import os

# firmware upload path
upload_root_folder_path = os.path.join('.', 'uploads')
backup_folder_path = os.path.join(upload_root_folder_path, 'backups')


class HTTPServer(object):
    app = Klein()
    connection_config = None
    hardware_engine = None
    required_input_files = None


    def __init__(self, connection_config, required_input_files):
        self.connection_config = connection_config
        self.required_input_files = required_input_files

    def addHardware(self, hw):
        self.hardware_engine = hw

    def start(self):
        self.app.run('0.0.0.0', self.connection_config["listening_port"])

    @app.route('/tb/grade_assignment/', methods=['POST'])
    def grade_assignment(self, request):
        input_files = {}
        for field in self.required_input_files:
            file_binary = request.args.get(field.encode())
            if file_binary is None:
                print('HTTPServer: Error: field "%s" is not specified' % field)
                #TODO: return code 403
                return "Missing field"
            input_files[field] = file_binary[0]

        if self.hardware_engine.request_grade_assignment(input_files):
            return "Will grade assignment"
        else:
            #TODO: return code 403
            return "Abort"
            
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

        # after upload the binaries to DUT, it takes some time to refresh
        self.hardware_engine.reset_dut()
        time.sleep(2.0)


        self.hardware_engine.reset_dut()

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
        self.hardware_engine.reset_dut()

        request.setHeader('Content-Type', 'text/plain')
        return "DUT [%s] reset request received" % dut_id

    # HARDWARE ENGINE RESET
    @app.route('/he/reset/', methods=['POST'])
    def tester_reset(self, request):
        print('resetting tester')

        # reset tester
        self.hardware_engine.reset_hardware_engine()

        request.setHeader('Content-Type', 'text/plain')
        return "Tester reset request received"

    # HARDWARE ENGINE START TEST
    @app.route('/tb/start/', methods=['POST'])
    def tester_start(self, request):
        print('starting test')

        waveform_path = os.path.join(upload_root_folder_path, 'input_waveform')
        
        # start testing
        self.hardware_engine.start_test(waveform_path)

        request.setHeader('Content-Type', 'text/plain')
        return "Tester start request received"

    # GET TESTER STATUS
    @app.route('/tb/status/', methods=['GET'])
    def tester_status(self, request):
        if not self.hardware_engine:
            return "ERROR_NOHARDWARE"
        else:
            print('Tester status requested')
            return self.hardware_engine.get_status()

