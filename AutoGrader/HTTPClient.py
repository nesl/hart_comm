# ===== IMPORTS =====
import requests

class HTTPClient(object):
	config = ''
	remote_port = 0
	remote_host = ''
	remote_http = ''

	def __init__(self, config):
		self.config = config
		self.remote_host = config["remotehost"]
		self.remote_port = config["remoteport"]
		self.remote_http = 'http://' + self.remote_host + ':' + str(self.remote_port)

	def send_tb_summary(self, summary):
		print summary
		r = requests.post( self.remote_http+'/tb/summary/'\
			, data={'summary': summary}, timeout=1.0)

	def send_tb_status(self, status):
		r = requests.post( self.remote_http+'/tb/status/'\
			, data={'status': status}, timeout=1.0)

	def send_waveform(self, fpath):
		files = {'waveform': ('waveform.txt', open(fpath, 'rb'), 'text/plain')}
		r = requests.post( self.remote_http+'/tb/waveform/', \
			data={'id':self.config["id"]}, files=files, timeout=5.0)