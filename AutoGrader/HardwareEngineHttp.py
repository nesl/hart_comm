import time
import threading
import os
import shutil
import datetime
import traceback
import importlib
import subprocess

from .HardwareEngine import HardwareEngine

class HardwareEngineHttp(HardwareEngine):

    def __init__(self, config):
        super(HardwareEngine, self).__init__(config)
    
        # variable initialization
        self.http_client = None
        self.task_secret_code = None

    def add_http_client(self, client):
        self.http_client = client

    def _terminate_hardware_procedure(self):
        # terminate all hardware devices
        super(Foo, self)._terminate_hardware_procedure()

        # upload files
        output_files = {}
        for file_name in self.config['required_output_files']:
            file_path = os.path.join(self.file_folder, file_name)
            output_files[file_name] = file_path
        
        if self.http_client.send_dut_output(output_files, self.task_secret_code):
            print('Output files uploaded')
        else:
            print('Unable to upload output to server')
        
        # update status over HTTP
        if self.http_client.send_tb_status(self.status):
            print('IDLE status sent')
        else:
            print('Unable to post status to server')

    def request_grade_task(self, input_files, secret_code, execution_time_sec):
        """
        Is designed for entities which wish to make an assignment grading request (expected from
        HTTPServer).

        Params:
          input_files: a dictionary of (string => bytestream). It is designed for passing file
              content from server side
          secret_code: the code to return when finishing the grading
          execution_time_sec: maximum time allowed to execute this task
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
        if execution_time_sec is None:
            execution_time_sec = 600

        self.grade_task(execution_time_sec)
        # start the grading task asynchronously
        print('request_grade_task start')
        threading.Thread(
                target=self._grade_thread,
                name=('id=%s' % self.config['id']),
                args=[exection_time_sec],
        ).start()

        return True

    #
    # Threads   
    #
    def _grade_thread(self, execution_time_sec):
        self.grade_task(execution_time_sec)
