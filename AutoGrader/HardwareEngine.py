# ========== IMPORTS ==========
import serial
import string
import time
import threading
from .UARTTransceiver import *

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
		print('type: %d, time: %d, val: %d' % (pktType, pktTime, pktVal))
		if pktType == ord(self.CMD_TERMINATE):
			self.status = 'IDLE'
			print('Test complete.')
			self.outfile.close()

			# stop listening to UART
			self.uart.stopListening()
			self.uart.close()

			# send results file over HTTP
			try:
				self.http_client.send_waveform( self.outfilepath )
				print('Waveform file uploaded')
			except:
				print('Unable to upload output to server')


			# update status over HTTP
			try:
				self.http_client.send_tb_status( 'IDLE' )
				print('IDLE status sent')
			except:
				print('Unable to post status to server')

			# re-open output file for saving test results
			self.outfile = open(self.outfilepath, 'wb')

			return

		# otherwise, we'll just write the outputs to a file
		self.outfile.write( '%d, %d, %d\n' % (pktType, pktTime, pktVal) )

	def get_status(self):
		return self.status

	def start_test(self, wavefile):
		# set status to busy
		self.status = 'TESTING'
		# start listening on UART
		self.uart.open()
		self.uart.startListening()		
		# open waveform file
		wfile = open(wavefile, 'rb')
		data = wfile.read()
		self.uart.write(data)

	def reset_dut(self):
		self.uart.sendCommand( self.CMD_RESET_DUT )

	def reset_tester(self):
		self.uart.sendCommand( self.CMD_RESET_TESTER )

	def enable_anlog_reading(self):
		self.uart.sendCommand( self.CMD_ENABLE_ANALOG )

