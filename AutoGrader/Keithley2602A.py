# Original Author: Bo-Jhang Ho
# Code from NESL at UCLA

import struct
import socket
import time
import sys
import re
import numpy
import datetime

from AutoGrader.HardwareBase import HardwareBase


class Keithley2602A(HardwareBase):
    # parameters
    host = None
    port = None
    energy_file_path = None
   
    # connection
	sock = None

	# status
	is_running = False

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
		self._send_abort_command()
		self.sock.send(b'reset()')
		self.sock.send(b'set_parameters()')
		self.sock.send(b'begin_supply()')
		
		self.is_running = True

		self.start_measurement_time = datetime.datetime.now()
		self.prev_measurement_time = self.start_measure_time
		self.accu_energy = 0.
        self.energy_grace = []

    def on_execute(self):
		while self.is_running:
			self._send_measure_command()
	
    def on_terminate(self):
		while self.is_running:
			pass
		with open(self.energy_file_path, 'w') as fo:
            for age, energy in self.energy_trace:
                f.write('%.f %.f' % (age, energy))

    def on_reset_after_execution(self):
		self.sock.send(b'end_supply()')
		self._send_abort_command()
		self.sock.close()
		self.sock = None

    def _send_abort_command(self):
        self.sock.send(b"*RST\n")
        self.sock.send(b"abort\n")
        self.sock.send(b"*CLS\n")
        
	def _send_measure_command(self):
        self.sock.send(b"measure()\n")
        buf = self.sock.recv(4096)
		buf.decode('ascii').split('\t')
		_, sensing_time, energy = tuple(map(float, buf.decode('ascii').split('\t')))
        cur_time = datetime.datetime.now()
        session_elasped_time = self._convert_timedelta_to_ms(cur_time - self.prev_measurement_time)
        session_energy = energy / elasped_time * session_elasped_time
        age = self._convert_timedelta_to_ms(cur_time - self.start_measurement_time)
        self.accu_energy += session_energy
        self.energy_trace.append((age, self.accu_energy))

    def _convert_timedelta_to_ms(self, dt):
        return dt.seconds + dt.microseconds * 1e-6
