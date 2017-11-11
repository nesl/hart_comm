import time
import threading
import os
import shutil
import datetime
import traceback
import importlib
import subprocess

class HardwareEngine(object):

    def __init__(self, config):
        self._initialize_variables()
        self._initialize_parsing_config(config)
    
    def grade_task(self, execution_time_sec):
        print('grade_task enter, set timer %f sec' % execution_time_sec)
        self._reset_devices()
        self.task_running = True
        self._start_test()
        self.aborting_task_timer = threading.Timer(
                execution_time_sec, self._terminate_hardware_procedure)
        self.aborting_task_timer.start()

    #
    # methods to handle devices
    #
    def _reset_devices(self):
        for hardware_name in self.hardware_processing_order:
            self.hardware_dict[hardware_name].on_before_execution()

    def _start_test(self):
        # notify all hardware the execution just begins
        self.execution_threads = []
        for hardware_name in self.hardware_processing_order:
            thread_name = 'Exe-%s' % hardware_name
            print('_start_test', thread_name)
            t = threading.Thread(name=thread_name,
                    target=self.hardware_dict[hardware_name].on_execute)
            t.start()
            self.execution_threads.append(t)
    
    def _terminate_hardware_procedure(self):
        if not self.task_running:
            return

        self.task_running = False

        self.aborting_task_timer.cancel()
        
        # send terminate signal to all hardware
        for hardware_name in self.hardware_processing_order:
            print('terminate', hardware_name)
            self.hardware_dict[hardware_name].on_terminate()

        for th in self.execution_threads:
            print('wait for', th)
            th.join()
        
        # send clean signal to all hardware
        for hardware_name in self.hardware_processing_order:
            self.hardware_dict[hardware_name].on_reset_after_execution()

        # backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        task_backup_folder = os.path.join(self.backup_root_folder, now)
        os.makedirs(task_backup_folder)
        shutil.move(self.file_folder, task_backup_folder)

    #
    # callbacks
    #
    def notify_terminate(self):
        """
        Expceted call-sites are hardware devices or aborting_task_timer
        """
        self._terminate_hardware_procedure()
    
    #
    # private initialization procedure
    #
    def _initialize_variables(self):
        # file storage
        self.file_folder = os.path.join('.', 'uploads')
        self.backup_root_folder = os.path.join('.', 'upload_backups')

        # testbed info
        self.config = None

        # hardware info
        self.hardware_dict = None
        self.hardware_processing_order = None

        # hardware execution
        self.execution_threads = None

        # grading status
        self.task_running = None
        self.task_execution_time_sec = None
        self.aborting_task_timer = None

    def _initialize_parsing_config(self, config):
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
