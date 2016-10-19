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
            r = requests.post( self.remote_http+'/tb/send-summary/',
                    data={'summary': summary},
                    headers={'content-type': "application/x-www-form-urlencoded"},
                    timeout=1.0)
        except:
            print('[Network Error] Remote server is down... Failed on sending summary messages')
            return False
        return True


    def send_tb_status(self, status):
        try:
            r = requests.post( self.remote_http+'/tb/send-status/',
                    data={'id':self.config["id"], 'status': status},
                    headers={'content-type': "application/x-www-form-urlencoded"},
                    timeout=1.0)
        except:
            print('[Network Error] Remote server is down... Failed on sending testbed status')
            return False
        return True

    def send_dut_output(self, f_waveform_path, f_log_path):
        try:
            data = {
                    'id': self.config["id"],
                    'num_duts': 1,
            }
            files = {
                    'dut0_waveform': ('waveform0.txt', open(f_waveform_path, 'rb'), 'text/plain'),
                    'dut0_serial_log': ('serial0.bin', open(f_log_path, 'rb'), 'text/plain'),
            }
            # The files can be big, wait longer time to transfer data back
            r = requests.post(self.remote_http + '/tb/send-dut-output/',
                    data=data, files=files, timeout=10.0)
        except:
            print('[Network Error] Cannot send grading result back to remote server')
            return False
        return True
