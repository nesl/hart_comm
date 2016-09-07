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
	callback = ''
	START_DELIM = 'S'
	STOP_DELIM = 'E'
	TOTAL_PKT_LEN = 9
	listening = False

	def __init__(self, baud, path, callback):
		threading.Thread.__init__(self, name="uartserial")

		self.baud_rate = baud
		self.dev_path = path
		self.callback = callback
		# flush the serial 
		self.dev = serial.Serial()

	def __del__(self):
		if self.dev.is_open:
			self.dev.close()

	def run(self):
		while True:
			if not self.listening:
				continue

			# continue immediately if serial isn't ready
			if not self.dev.is_open:
				continue

			# wait for 9 bytes (full packet)
			while self.dev.inWaiting() < self.TOTAL_PKT_LEN:
				pass

			# read in the full packet
			rxBuffer = []
			for i in range(self.TOTAL_PKT_LEN):
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
		was_open = self.dev.is_open
		if not was_open:
			self.open()

		payload = self.START_DELIM + cmd + "000000" + self.STOP_DELIM
		self.dev.write(payload.encode())

		if not was_open:
			self.close()

	def write(self, data):
		was_open = self.dev.is_open
		if not was_open:
			self.open()

		self.dev.write(data)

		if not was_open:
			self.close()

	def close(self):
		try:
			self.dev.flush()
			self.dev.close()
		except:
			print('UART device unable to close')

	def open(self):
		self.dev = serial.Serial()
		self.dev.port = self.dev_path    
		self.dev.baudrate = self.baud_rate    
		self.dev.parity=serial.PARITY_NONE
		self.dev.bytesize=serial.EIGHTBITS
		self.dev.stopbits=serial.STOPBITS_ONE
		self.dev.timeout=None
		self.dev.writeTimeout=None
		try:
			self.dev.open() 
		except:
			print('UART device unable to open')

	def startListening(self):
		self.listening = True

	def stopListening(self):
		self.listening = False



