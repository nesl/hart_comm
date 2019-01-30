import requests

class HTTPClient(object):

    def __init__(self, config, server_listening_port):
        remote_host = config["remotehost"]
        http_s = 's' if 'use_https' in config and config['use_https'] else ''
        self.ssl_verify = False if 'ssl_verify' in config and not config['ssl_verify'] else True
        port_prefix = (':%d' % config["remoteport"]) if 'remoteport' in config else ''
        
        self.remote_http = 'http%s://%s%s' % (http_s, remote_host, port_prefix)
        self.report_listening_port = server_listening_port

    def send_tb_summary(self, testbed_type, status):
        try:
            r = requests.post(self.remote_http + '/tb/send-summary/',
                    data={
                            'localport': self.report_listening_port,
                            'testbed_type': testbed_type,
                            'status': status,
                    },
                    headers={'content-type': "application/x-www-form-urlencoded"},
                    timeout=1.0,
                    verify=self.ssl_verify,
            )
            if r.status_code != 200:
                print('[Request Error] Server rejected the request')
                return False
        except:
            #TODO: delete these
            import traceback
            import sys
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            print('[Network Error] Remote server is down... Failed on sending summary messages')
            return False
        return True

    def send_tb_status(self, status):
        try:
            r = requests.post(self.remote_http + '/tb/send-status/',
                    data={'localport': self.report_listening_port, 'status': status},
                    headers={'content-type': "application/x-www-form-urlencoded"},
                    timeout=1.0,
                    verify=self.ssl_verify,
            )
            if r.status_code != 200:
                print('[Request Error] Server rejected the request')
                return False
        except:
            print('[Network Error] Remote server is down... Failed on sending testbed status')
            return False
        return True

    def send_dut_output(self, output_file_dict, secret_code):
        try:
            data = {'localport': self.report_listening_port, 'secret_code': secret_code}
            files = {}
            for file_name in output_file_dict:
                field_name = "file_" + file_name
                files[field_name] = (
                        field_name, open(output_file_dict[file_name], 'rb'), 'text/plain')
            # The files can be big, wait longer time to transfer data back
            r = requests.post(self.remote_http + '/tb/send-dut-output/',
                    data=data, files=files, timeout=10.0, verify=self.ssl_verify)
            if r.status_code != 200:
                print('[Request Error] Server rejected the request')
                return False
        except:
            print('[Network Error] Cannot send grading result back to remote server')
            import sys
            import traceback
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_tb)
            return False
        return True
