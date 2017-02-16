import requests

class HTTPClient(object):
    remote_http = None

    def __init__(self, config):
        remote_host = config["remotehost"]
        http_s = 's' if 'use_https' in config and config['use_https'] else ''
        port_prefix = (':%d' % config["remoteport"]) if 'remoteport' in config else ''
        self.remote_http = 'http%s://%s%s' % (http_s, remote_host, port_prefix)

    def send_tb_summary(self, summary):
        try:
            r = requests.post(self.remote_http + '/tb/send-summary/',
                    data={'summary': summary},
                    headers={'content-type': "application/x-www-form-urlencoded"},
                    timeout=1.0)
        except:
            print('[Network Error] Remote server is down... Failed on sending summary messages')
            return False
        return True

    def send_tb_status(self, status):
        try:
            r = requests.post(self.remote_http + '/tb/send-status/',
                    data={'id':self.config["id"], 'status': status},
                    headers={'content-type': "application/x-www-form-urlencoded"},
                    timeout=1.0)
        except:
            print('[Network Error] Remote server is down... Failed on sending testbed status')
            return False
        return True

    def send_dut_output(self, output_file_dict):
        try:
            data = {'id': self.config["id"]}
            files = {}
            for field in output_file_dict:
                files[field] = (field, open(output_file_dict[field], 'rb'), 'text/plain')
            # The files can be big, wait longer time to transfer data back
            r = requests.post(self.remote_http + '/tb/send-dut-output/',
                    data=data, files=files, timeout=10.0)
        except:
            print('[Network Error] Cannot send grading result back to remote server')
            import sys
            import traceback
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_tb)
            return False
        return True
