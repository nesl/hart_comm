# Original Author: Bo-Jhang Ho
# Code from NESL at UCLA

import struct
import socket
import time
import numpy
import datetime
import os

from AutoGrader.devices import HardwareBase


class Keithley2602A(HardwareBase):
    # parameters
    host = None
    port = None
    energy_file_path = None
   
    # connection
    sock = None

    # status
    is_running = False
    is_measuring = False

    # statistics
    start_measurement_time = None
    prev_measurement_time = None
    accu_energy = None
    energy_trace = None

    def __init__(self, name, config, hardware_engine, file_folder):
        if "host" not in config:
            raise Exception('"host" field is required')
        self.host = config['host']
    
        if "port" not in config:
            raise Exception('"port" field is required')
        self.port = config['port']
        
        if "output_energy_file" not in config:
            raise Exception('"output_energy_file" field is required')
        self.energy_file_path = os.path.join(file_folder, config['output_energy_file'])

    def on_before_execution(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.sock.send(b'TSB_Script.run()\n')
        #self._send_abort_command()
        #self.sock.send(b'reset()\n')
        #self.sock.send(b'set_parameters()\n')
        #self.sock.send(b'begin_supply()\n')
        
        self.is_running = True
        self.is_measuring = False

    def on_execute(self):
        self.start_measurement_time = datetime.datetime.now()
        self.prev_measurement_time = self.start_measurement_time
        self.accu_energy = 0.
        self.energy_trace = []
        while self.is_running:
            self._send_measure_command()
    
    def on_terminate(self):
        self.is_running = False
        while self.is_measuring:
            pass
        with open(self.energy_file_path, 'w') as fo:
            for age, energy in self.energy_trace:
                fo.write('%f %f\n' % (age, energy))
                print('Keithley', age, energy)

    def on_reset_after_execution(self):
        #self.sock.send(b'end_supply()\n')
        #self._send_abort_command()
        self.sock.close()
        self.sock = None

    def _send_abort_command(self):
        self.sock.send(b"*RST\n")
        self.sock.send(b"abort\n")
        self.sock.send(b"*CLS\n")
        
    def _send_measure_command(self):
        self.is_measuring = True
        self.sock.send(b"measure()\n")
        buf = self.sock.recv(4096)
        buf.decode('ascii').split('\t')
        _, sensing_time, energy = tuple(map(float, buf.decode('ascii').split('\t')))
        cur_time = datetime.datetime.now()
        session_elapsed_time = self._convert_timedelta_in_ms_precision(cur_time - self.prev_measurement_time)
        session_energy = energy / sensing_time * session_elapsed_time
        age = self._convert_timedelta_in_ms_precision(cur_time - self.start_measurement_time)
        print('age', age)
        self.accu_energy += session_energy
        self.energy_trace.append((age, self.accu_energy))
        self.prev_measurement_time = cur_time
        self.is_measuring = False

    def _convert_timedelta_in_ms_precision(self, dt):
        return dt.seconds + dt.microseconds * 1e-6
