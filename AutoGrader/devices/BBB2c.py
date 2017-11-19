import sys
import traceback
import shutil
import os
import time
import subprocess

from AutoGrader.devices import HardwareBase

class BBB2c(HardwareBase):
    """
    For timestamping events
    """

    def __init__(self, name, config, hardware_engine, file_folder):
        
        # parameters
        self.linux_binary_path = None
        self.pru_binary_path = None
        self.output_path = None
        self.stdout_path = None
        self.stderr_path = None

        # device info
        self.name = None
        self.config = None

        # parse config
        if "linux_binary_file" not in config:
            raise Exception('"linux_binary_file" field is required')
        self.linux_binary_path = os.path.join(file_folder, config['linux_binary_file'])
        
        if "pru_binary_file" not in config:
            raise Exception('"pru_binary_file" field is required')
        self.pru_binary_path = os.path.join(file_folder, config['pru_binary_file'])
        
        if "output_file" not in config:
            raise Exception('"output_file" field is required')
        self.output_path = os.path.join(file_folder, config['output_file'])

        if "stdout_file" not in config:
            raise Exception('"stdout_file" field is required')
        self.stdout_path = os.path.join(file_folder, config['stdout_file'])

        if "stderr_file" not in config:
            raise Exception('"stderr_file" field is required')
        self.stderr_path = os.path.join(file_folder, config['stderr_file'])

        self.name = name
        self.config = config

    def on_before_execution(self):
        subprocess.call(['ssh', 'root@192.168.7.2', 'testenv/prepare.sh'])
        subprocess.call(['scp', self.linux_binary_path, 'root@192.168.7.2:~/testenv/files/student_bin'])
        subprocess.call(['scp', self.pru_binary_path, 'root@192.168.7.2:~/testenv/files/pru_bin'])

    def on_execute(self):
        subprocess.call(['ssh', 'root@192.168.7.2', 'testenv/run.py', 'pru_bin', 'student_output.txt'])

    def on_terminate(self):
        subprocess.call(['scp', 'root@192.168.7.2:~/testenv/files/student_output.txt', self.output_path])
        subprocess.call(['scp', 'root@192.168.7.2:~/testenv/files/stdout.txt', self.stdout_path])
        subprocess.call(['scp', 'root@192.168.7.2:~/testenv/files/stderr.txt', self.stderr_path])
    
    def on_reset_after_execution(self):
        pass
