#!/usr/bin/python

# -- imports --
import os
import re
import serial
import numpy as np
import threading

class UARTTransceiver(threading.Thread):
	# class variables
	baud_rate = 115200
	dev_path = '/dev/'
	dev_name = ''
	dev = ''
	dev_status = 0
	callback = ''

	def __init__(self, baud, callback):
		threading.Thread.__init__(self, name="uarterial")

		self.baud_rate = baud
		# initialize callback function
		self.callback = callback

		# first locate the mbed object
		devs = os.listdir(self.dev_path)
		for fname in devs:
			if re.match('.*tty\.usbmodem.*',fname) or re.match('.*ACM0.*', fname):
				print('opening serial: ' + fname)
				self.dev_name = fname
				break
		if self.dev_name != '':
			# now open this device for reading
			self.dev = serial.Serial(self.dev_path+self.dev_name, baudrate=self.baud_rate)
			self.dev_status = 1

			# flush the serial 
			self.flush()
		else:
			print('could not find mbed!')

	def __del__(self):
		if self.dev_status == 1:
			self.dev.close()

	def run(self):
		while True:
			# continue immediately if serial isn't ready
			if self.dev_status == 0:
				continue

			# read new line
			line = self.dev.readline()
			try:
				decodeline = line.decode("utf-8")
				self.handleData(decodeline)
			except:
				print('skipping bad packet')

	def handleData(self, data):
		line = data.strip().split(',')

		# check to make sure it's a proper packet
		try:
			team_id = float(line[0])
			cmd_type = float(line[1])
			value = float(line[2]) 
		except Exception:
			print('ignoring bad packet')
			return 0

		self.callback(int(team_id), int(cmd_type), int(value))


	def flush(self):
		self.dev.flushInput()
		self.dev.flush()

		


	



