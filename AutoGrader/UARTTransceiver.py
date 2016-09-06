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
	dev_path = ''
	dev = ''
	dev_status = 0
	callback = ''
	START_DELIM = 'S'
	STOP_DELIM = 'E'
	TOTAL_PKT_LEN = 9

	def __init__(self, baud, path, callback):
		threading.Thread.__init__(self, name="uartserial")

		self.baud_rate = baud
		self.dev_path = path
		self.callback = callback
		
		if self.dev_path != '':
			# now open this device for reading
			self.dev = serial.Serial()
			self.dev.port = self.dev_path    
			self.dev.baudrate = self.baud_rate    
			self.dev.parity=serial.PARITY_NONE
			self.dev.bytesize=serial.EIGHTBITS
			self.dev.stopbits=serial.STOPBITS_ONE
			self.dev.timeout=1
			self.dev.writeTimeout=None
			self.dev.open() 

			self.dev_status = 1
			# flush the serial 
			self.flush()
		else:
			raise Exception('Could not open UART device')

	def __del__(self):
		if self.dev_status == 1:
			self.dev.close()

	def run(self):
		while True:
			# continue immediately if serial isn't ready
			if self.dev_status == 0:
				continue

			# wait for start byte
			while self.dev.read() != self.START_DELIM:
				pass

			# read in the rest of the packet
			rxBuffer = []
			for i in xrange(TOTAL_PKT_LEN - 2):
				rxBuffer.append( self.dev.read() )

			# check stop byte
			if self.dev.read() != self.STOP_DELIM:
				# bad packet
				continue

			# if we got this far, we have a (potentially) good packet to parse
			handleData( rxBuffer )

	def handleData(self, data):
		# 1B type, 4B time, 2B val
		try:
			[pktType, pktTime, pktVal] = struct.unpack('<BLH')
		except Exception:
			# ignoring bad packet
			pass

		self.callback(pktType, pktTime, pktVal)

	def flush(self):
		self.dev.flushInput()
		self.dev.flush()

	def sendCommand(self, cmd):
		payload = self.START_DELIM + cmd + "000000" + self.STOP_DELIM
		self.dev.write(payload)

	def write(self, data):
		self.dev.write(data)

	def close(self):
		self.dev.close()

		


	



