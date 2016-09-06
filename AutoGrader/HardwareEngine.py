# ========== IMPORTS ==========
import serial
import string
import time
import threading
from UARTTransceiver import *

class HardwareEngine(object):
	status = 'IDLE'
	config = ''
	uart = None
	baudrate = 460800
	CMD_RESET_DUT = 'U'
	CMD_RESET_TESTER = 'R'
	CMD_ENABLE_ANALOG = 'O'
	CMD_TERMINATE = 'E'
	outfilepath = 'uploads/output.txt'
	outfile = None
	http_client = None

	def __init__(self, config):
		# copy config JSON
		self.config = config
		# init UART transceiver
		self.uart = UARTTransceiver(self.baudrate, self.config["tester"]["path"], self.on_data_rx)
		self.uart.start()
		# open output file for saving test results
		self.outfile = open(self.outfilepath, 'wb')

	def add_http_client(self, client):
		self.http_client = client

	def on_data_rx(self, pktType, pktTime, pktVal):
		# if termination is received, change status and close file
		if pktType == self.CMD_TERMINATE:
			self.status = 'IDLE'
			self.uart.close()
			self.uart.stop()
			self.outfile.close()

			# send results file over HTTP
			self.http_client.send_waveform( self.outfilepath )

			# update status over HTTP
			self.http_client.send_status( 'IDLE' )
			return

		# otherwise, we'll just write the outputs to a file
		self.outfile.writeline( '%d, %d, %d\n' % (pktType, pktTime, pktVal) )

	def get_status(self):
		return self.status

	def start_test(self, wavefile):
		# set status to busy
		self.status = 'TESTING'
		# open waveform file
		wavfile = open(wavfile, 'rb')
		data = wavfile.read()
		self.uart.write(data)

	def reset_dut(self):
		uart.sendCommand( self.CMD_RESET_DUT )

	def reset_tester(self):
		uart.sendCommand( self.CMD_RESET_TESTER )

	def enable_anlog_reading(self):
		uart.sendCommand( self.CMD_ENABLE_ANALOG )

