import requests

class HTTPClient(object):
    config = None
    remote_port = None
    remote_host = None
    remote_http = None

    def __init__(self, config):
        self.config = config
        self.remote_host = config["remotehost"]
        self.remote_port = config["remoteport"]
        self.remote_http = 'https://%s' % (self.remote_host)

    def send_tb_summary(self, summary):
        try:
            r = requests.post( self.remote_http+'/tb/summary/',
                    data={'summary': summary},
                    headers={'content-type': "application/x-www-form-urlencoded"},
                    timeout=1.0, verify=False)
        except requests.exceptions.ConnectionError:
            print('[Network Error] Remote server is down... Failed on sending summary messages')
            return False
        return True


    def send_tb_status(self, status):
        try:
            r = requests.post( self.remote_http+'/tb/status/',
                    data={'id':self.config["id"], 'status': status},
                    headers={'content-type': "application/x-www-form-urlencoded"},
                    timeout=1.0, verify=False)
        except requests.exceptions.ConnectionError:
            print('[Network Error] Remote server is down... Failed on sending testbed status')
            return False
        return True

    def send_waveform(self, fpath):
        try:
            files = {'waveform': ('waveform.txt', open(fpath, 'rb'), 'text/plain')}
            r = requests.post( self.remote_http+'/tb/waveform/',
                    data={'id':self.config["id"]},
                    files=files,
                    timeout=5.0, verify=False)
        except requests.exceptions.ConnectionError:
            print('[Network Error] Cannot send grading result back to remote server')
            return False
        return True
