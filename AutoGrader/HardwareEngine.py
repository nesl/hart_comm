import serial
import string
import time
import threading
import os
import shutil
import datetime
import traceback
import importlib

from .UART_HE_Transceiver import *
from .UART_DUT_Transceiver import *


# output generation path
upload_root_folder_path = os.path.join('.', 'uploads')
backup_folder_path = os.path.join(upload_root_folder_path, 'backups')


class HardwareEngine(object):
    STATUS_IDLE = "IDLE"
    STATUS_BUSY = "TESTING"

    status = STATUS_IDLE
    config = None

    hardware_dict = None
    hardware_init_order = None

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
            instance = MyClass(hardware_name, init_params, self)
            self.hardware_dict[hardware_name] = instance
        
    def add_http_client(self, client):
        self.http_client = client

    def get_status(self):
        return self.status

    def start_test(self, wavefile_name):
        # set status to busy
        self.status = STATUS_TESTING

        # notify all hardware the execution just begins
        for hardware_name in self.hardware_dict:
            self.hardware_dict[hardware_name].on_execute()
        
        #TODO: when about to start the test, set a deadline

    def reset_devices(self):
        for hardware_name in self.hardware_dict:
            self.hardware_dict[hardware_name].on_before_execution()

    def notify_terminate(self):
        self._terminate_hardware_procedure()
        
    def _terminate_hardware_procedure(self):
        # send terminate signal to all hardware
        for hardware_name in self.hardware_dict:
            self.hardware_dict[hardware_name].on_terminate()

        # backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        
        backup_output_dir = os.path.join(backup_folder_path, 'output', now)
        os.makedirs(backup_output_dir)
        output_files = {}
        for file_name in self.config['required_output_files']:
            #TODO: upload_folder + file_name
            shutil.copy(file_name, backup_output_dir)
            output_files[file_name] = file_name
        
        if self.http_client.send_dut_output(output_files):
            print('Waveform file uploaded')
        else:
            print('Unable to upload output to server')
        
        # send clean signal to all hardware
        for hardware_name in self.hardware_dict:
            self.hardware_dict[hardware_name].on_reset_after_execution()

        # all tasks are done. update status
        self.status = STATUS_IDLE
        print('Test complete.')

        # update status over HTTP
        if self.http_client.send_tb_status(self.status):
            print('IDLE status sent')
        else:
            print('Unable to post status to server')
        
    def request_grade_assignment(self, input_files, secret_code):
        """
        Return:
          True if succesfully storing the data
        """
        #TODO: store input files somewhere
        #TODO: create a new thread to start the grading thing
        return True
