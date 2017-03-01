import serial
import string
import time
import threading
import os
import shutil
import datetime
import traceback
import importlib


class HardwareEngine(object):
    STATUS_IDLE = "IDLE"
    STATUS_TESTING = "TESTING"

    # file storage
    file_folder = os.path.join('.', 'uploads')
    backup_root_folder = os.path.join(file_folder, 'backups')

    # testbed info
    status = STATUS_IDLE
    config = None

    # hardware info
    hardware_dict = None
    hardware_init_order = None

    # grading status
    task_secret_code = None
    task_running = None
    task_execution_time_sec = None
    abort_task_timer = None

    def __init__(self, config):
        self.config = config
        hardware_dict = config['hardware_list']

        # get hardware initialization order
        if not 'hardware_init_order' in config:
            self.hardware_init_order = []
            for hardware_name in config['hardware_list']:
                self.hardware_init_order.append(hardware_name)
        else:
            self.hardware_init_order = config['hardware_init_order']
            if len(self.hardware_init_order) != len(config['hardware_list']):
                raise Exception('hardware_list and hardware_init_order do not match in configuration file')
            for hardware_name in self.hardware_init_order:
                if hardware_name not in config['hardware_list']:
                    raise Exception('hardware_list and hardware_init_order do not match in configuration file')

        self.hardware_dict = {}
        for hardware_name in config['hardware_list']:
            hardware_config = config['hardware_list'][hardware_name]
            init_params = hardware_config['init_params']
            module_name, class_name = hardware_config['class'].rsplit(".", 1)
            MyClass = getattr(importlib.import_module(module_name), class_name)
            instance = MyClass(hardware_name, init_params, self, self.file_folder)
            self.hardware_dict[hardware_name] = instance

        for input_file in config['required_input_files']:
            if input_file in config['required_output_files']:
                raise Exception('required_input_files and required_output_files are overlapped')

        # prepare upload folder
        if not os.path.isdir(self.file_folder):
            os.makedirs(self.file_folder)
        
    def add_http_client(self, client):
        self.http_client = client

    def get_status(self):
        return self.status

    def reset_devices(self):
        for hardware_name in self.hardware_dict:
            self.hardware_dict[hardware_name].on_before_execution()

    def start_test(self):
        # notify all hardware the execution just begins
        for hardware_name in self.hardware_dict:
            self.hardware_dict[hardware_name].on_execute()
        
    def notify_terminate(self):
        self._terminate_hardware_procedure()
        
    def _terminate_hardware_procedure(self):
        if not self.task_running:
            return

        self.task_running = False

        self.abort_task_timer.cancel()
        
        # send terminate signal to all hardware
        for hardware_name in self.hardware_dict:
            self.hardware_dict[hardware_name].on_terminate()

        # backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        
        task_backup_folder = os.path.join(self.backup_root_folder, now)
        os.makedirs(task_backup_folder)
        output_files = {}
        for file_name in self.config['required_output_files']:
            file_path = os.path.join(self.file_folder, file_name)
            shutil.copy(file_path, task_backup_folder)
            output_files[file_name] = file_path
        
        if self.http_client.send_dut_output(output_files, self.task_secret_code):
            print('Waveform file uploaded')
        else:
            print('Unable to upload output to server')
        
        # send clean signal to all hardware
        for hardware_name in self.hardware_dict:
            self.hardware_dict[hardware_name].on_reset_after_execution()

        # all tasks are done. update status
        self.status = self.STATUS_IDLE
        print('Test complete.')

        # update status over HTTP
        if self.http_client.send_tb_status(self.status):
            print('IDLE status sent')
        else:
            print('Unable to post status to server')

    def _grade_thread(self):
        self.reset_devices()
        self.task_running = True
        self.start_test()
        self.abort_task_timer = threading.Timer(
                self.task_execution_time_sec, self._terminate_hardware_procedure)
        self.abort_task_timer.start()

    def request_grade_assignment(self, input_files, secret_code, execution_time_sec):
        """
        Return:
          True if succesfully storing the data
        """
        if self.status != self.STATUS_IDLE:
            return False
        
        self.status = self.STATUS_TESTING

        # store assignment info
        for file_name in input_files:
            file_path = os.path.join(self.file_folder, file_name)
            with open(file_path, 'wb') as fo:
                fo.write(input_files[file_name])
        self.task_secret_code = secret_code
        self.task_execution_time_sec = execution_time_sec if execution_time_sec else 600

        # start the grading task asynchronously
        threading.Thread(target=self._grade_thread, name=('id=%s' % self.config['id'])).start()

        return True
