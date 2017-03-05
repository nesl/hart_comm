import time
import threading
import os
import shutil
import datetime
import traceback
import importlib
import subprocess

class HardwareEngine(object):
    STATUS_IDLE = "IDLE"
    STATUS_TESTING = "TESTING"

    # file storage
    file_folder = os.path.join('.', 'uploads')
    backup_root_folder = os.path.join('.', 'upload_backups')

    # testbed info
    status = STATUS_IDLE
    config = None

    # hardware info
    hardware_dict = None
    hardware_processing_order = None

    # hardware execution
    execution_threads = None

    # grading status
    task_secret_code = None
    task_running = None
    task_execution_time_sec = None
    aborting_task_timer = None

    def __init__(self, config):
        self.config = config
        hardware_dict = config['hardware_list']

        # get hardware initialization order
        if not 'hardware_processing_order' in config:
            self.hardware_processing_order = []
            for hardware_name in config['hardware_list']:
                self.hardware_processing_order.append(hardware_name)
        else:
            self.hardware_processing_order = config['hardware_processing_order']
            if len(self.hardware_processing_order) != len(config['hardware_list']):
                raise Exception('hardware_list and hardware_processing_order do not match in configuration file')
            for hardware_name in self.hardware_processing_order:
                if hardware_name not in config['hardware_list']:
                    raise Exception('hardware_list and hardware_processing_order do not match in configuration file')

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

        # prepare backup upload folder
        if not os.path.isdir(self.backup_root_folder):
            os.makedirs(self.backup_root_folder)
        
    def add_http_client(self, client):
        self.http_client = client

    def get_status(self):
        return self.status

    def reset_devices(self):
        for hardware_name in self.hardware_processing_order:
            self.hardware_dict[hardware_name].on_before_execution()

    def start_test(self):
        # notify all hardware the execution just begins
        self.execution_threads = []
        for hardware_name in self.hardware_processing_order:
            thread_name = 'Exe-%s' % hardware_name
            print('start_test', thread_name)
            t = threading.Thread(name=thread_name,
                    target=self.hardware_dict[hardware_name].on_execute)
            t.start()
            self.execution_threads.append(t)
        
    def notify_terminate(self):
        self._terminate_hardware_procedure()
        
    def _terminate_hardware_procedure(self):
        if not self.task_running:
            return

        self.task_running = False

        print(self)
        print(self.aborting_task_timer)
        self.aborting_task_timer.cancel()
        
        # send terminate signal to all hardware
        for hardware_name in self.hardware_processing_order:
            print('terminate', hardware_name)
            self.hardware_dict[hardware_name].on_terminate()

        for th in self.execution_threads:
            print('wait for', th)
            th.join()

        output_files = {}
        for file_name in self.config['required_output_files']:
            file_path = os.path.join(self.file_folder, file_name)
            output_files[file_name] = file_path
        
        if self.http_client.send_dut_output(output_files, self.task_secret_code):
            print('Waveform file uploaded')
        else:
            print('Unable to upload output to server')
        
        # send clean signal to all hardware
        for hardware_name in self.hardware_processing_order:
            self.hardware_dict[hardware_name].on_reset_after_execution()

        # backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        task_backup_folder = os.path.join(self.backup_root_folder, now)
        os.makedirs(task_backup_folder)
        shutil.move(self.file_folder, task_backup_folder)

        # all tasks are done. update status
        self.status = self.STATUS_IDLE
        print('Test complete.')

        # update status over HTTP
        if self.http_client.send_tb_status(self.status):
            print('IDLE status sent')
        else:
            print('Unable to post status to server')

    def _grade_thread(self):
        print('_grade_thread')
        self.reset_devices()
        self.task_running = True
        self.start_test()
        self.aborting_task_timer = threading.Timer(
                self.task_execution_time_sec, self._terminate_hardware_procedure)
        print('_grade_thread', self.aborting_task_timer)
        self.aborting_task_timer.start()

    def request_grade_assignment(self, input_files, secret_code, execution_time_sec):
        """
        Return:
          True if succesfully storing the data
        """
        if self.status != self.STATUS_IDLE:
            return False
        
        self.status = self.STATUS_TESTING

        # store assignment info
        if not os.path.isdir(self.file_folder):
            os.makedirs(self.file_folder)
        subprocess.call(['rm', '-rf', '%s/*' % self.file_folder])
        for file_name in input_files:
            file_path = os.path.join(self.file_folder, file_name)
            with open(file_path, 'wb') as fo:
                fo.write(input_files[file_name])
        self.task_secret_code = secret_code
        self.task_execution_time_sec = execution_time_sec if execution_time_sec else 600

        print('request_grade_assignment')
        # start the grading task asynchronously
        threading.Thread(target=self._grade_thread, name=('id=%s' % self.config['id'])).start()

        return True
