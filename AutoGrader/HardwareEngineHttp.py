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

    STATUS_IDLE = "IDLE"
    STATUS_TESTING = "TESTING"

    def __init__(self, config, file_folder, backup_root_folder):
        super().__init__(config, file_folder)
    
        # variable initialization
        self.http_client = None
        self.task_secret_code = None
        self.status = HardwareEngineHttp.STATUS_IDLE
        self.backup_root_folder = backup_root_folder

        # prepare backup upload folder
        if not os.path.isdir(self.backup_root_folder):
            os.makedirs(self.backup_root_folder)

    def add_http_client(self, client):
        self.http_client = client

    def _terminate_hardware_procedure(self):
        # _terminate_hardware_procedure() may be called several times by different devices, but
        # should only be executed once. We use self.task_running as an indicator of whether
        # the method has been called before, and the variable is changed in
        # HardwareEngine._terminate_hardware_procedure().
        if not self.task_running:
            return

        super()._terminate_hardware_procedure()

        # upload files
        output_files = {}
        for file_name in self.config['required_output_files']:
            file_path = os.path.join(self.file_folder, file_name)
            output_files[file_name] = file_path
        
        if self.http_client.send_dut_output(output_files, self.task_secret_code):
            print('Output files uploaded')
        else:
            print('Unable to upload output to server')
        
        # backup
        now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
        task_backup_folder = os.path.join(self.backup_root_folder, now)
        os.makedirs(task_backup_folder)
        shutil.move(self.file_folder, task_backup_folder)
        
        # all tasks are done. update status
        self.status = HardwareEngineHttp.STATUS_IDLE
        print('Test complete.')
    
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

        if self.status != HardwareEngineHttp.STATUS_IDLE:
            return False
        
        self.status = HardwareEngineHttp.STATUS_TESTING

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

        # start the grading task asynchronously
        print('request_grade_task start')
        threading.Thread(
                target=self._grade_thread,
                name=('id=%s' % self.config['id']),
                args=[execution_time_sec],
        ).start()

        return True

    #
    # query status
    #
    def get_status(self):
        return self.status

    #
    # Threads   
    #
    def _grade_thread(self, execution_time_sec):
        self.grade_task(execution_time_sec)
