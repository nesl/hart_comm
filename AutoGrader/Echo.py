import os
import time

from AutoGrader.HardwareBase import HardwareBase


class Echo(HardwareBase):
    # parameters
    input_path = None
    output_path = None

    # device info
    name = None
    config = None

    # parent
    hardware_engine = None

    # serial
    dev = None

    # files
    fin = None
    fout = None

    # thread status
    alive = True

    def __init__(self, name, config, hardware_engine, file_folder):
        if not 'input_file' in config:
            raise Exception('"input_file" field is required')
        self.input_path = os.path.join(file_folder, config['input_file'])

        if not 'output_file' in config:
            raise Exception('"output_file" field is required')
        self.output_path = os.path.join(file_folder, config['output_file'])

        self.name = name
        self.config = config
        self.hardware_engine = hardware_engine

    def on_before_execution(self):
        self.alive = True

    def on_execute(self):
        self.fin = open(self.input_path, 'r')
        self.fout = open(self.output_path, 'w')
        
        time.sleep(5)
        if self.alive:
            line = self.fin.readline()
            self.fout.write(line)
            if line == "TERMINATE":
                self.hardware_engine.notify_terinate()

    def on_terminate(self):
        self.alive = False
        self.fin.close()
        self.fout.close()
