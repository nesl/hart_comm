# ========== IMPORTS ==========
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
        r = requests.post( self.remote_http+'/tb/summary/', data={'summary': summary}, \
            headers={'content-type': "application/x-www-form-urlencoded"}, timeout=1.0)

    def send_tb_status(self, status):
        r = requests.post( self.remote_http+'/tb/status/', data={'id':self.config["id"], 'status': status}, \
            headers={'content-type': "application/x-www-form-urlencoded"}, timeout=1.0)

    def send_waveform(self, fpath):
        files = {'waveform': ('waveform.txt', open(fpath, 'rb'), 'text/plain')}
        r = requests.post( self.remote_http+'/tb/waveform/', \
            data={'id':self.config["id"]}, files=files, timeout=5.0)
