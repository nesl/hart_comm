#!/usr/bin/python

# -- imports --
import os
import re
import serial
import threading
import struct

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
			self.dev.timeout=None
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

			# wait for 9 bytes (full packet)
			while self.dev.in_waiting < self.TOTAL_PKT_LEN:
				pass

			# read in the full packet
			rxBuffer = []
			for i in xrange(self.TOTAL_PKT_LEN):
				rxBuffer.append( self.dev.read() )

			# check start and stop byte
			if rxBuffer[0] != self.START_DELIM or rxBuffer[8] != self.STOP_DELIM:
				# bad packet
				self.flush()
				continue

			# if we got this far, we have a (potentially) good packet to parse
			self.handleData( ''.join(rxBuffer[1:8]) )

	def handleData(self, data_string):
		# 1B type, 4B time, 2B val
		[pktType, pktTime, pktVal] = struct.unpack('<BLH', data_string)
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
		self.dev_status = 0;
		self.dev.close()

		


	



