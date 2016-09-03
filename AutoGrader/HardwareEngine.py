# ========== IMPORTS ==========
import serial

class HardwareEngine(object):
	status = 'IDLE'
	config = ''
	tty = None
	baudrate = 0

	def __init__(self, config):
		self.config = config

	def getStatus(self):
		return self.status

	def startTest(self, wavefile):
		pass

	def reset(self):
		pass

	def _sendCommand(self):
		pass