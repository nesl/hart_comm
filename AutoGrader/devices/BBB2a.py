import sys
import traceback
import shutil
import os
import time
import subprocess

from AutoGrader.devices import HardwareBase

class BBB2a(HardwareBase):
    """
    For timestamping events
    """

    def __init__(self, name, config, hardware_engine, file_folder):
        
        # parameters
        self.binary_path = None
        self.output_path = None

        # device info
        self.name = None
        self.config = None

        # parse config
        if "binary_file" not in config:
            raise Exception('"binary_file" field is required')
        self.binary_path = os.path.join(file_folder, config['binary_file'])
        
        if "output_file" not in config:
            raise Exception('"output_file" field is required')
        self.output_path = os.path.join(file_folder, config['output_file'])

        self.name = name
        self.config = config

    def on_before_execution(self):
        subprocess.call(['ssh', 'root@192.168.7.2', 'testenv/clean.sh'])
        subprocess.call(['scp', self.binary_path, 'root@192.168.7.2:~/testenv/files/student_bin'])

    def on_execute(self):
        subprocess.call(['ssh', 'root@192.168.7.2', 'testenv/run.py', 'student_output.txt'])

    def on_terminate(self):
        subprocess.call(['scp', 'root@192.168.7.2:~/testenv/files/student_output.txt', self.output_path])
    
    def on_reset_after_execution(self):
        pass
