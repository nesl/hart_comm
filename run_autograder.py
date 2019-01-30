import json
import sys
import signal
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

from AutoGrader import HardwareEngineHttp
from AutoGrader.http import HTTPServer, HTTPClient


# send testbed summary
def send_summary(http_client, config):
    try:
        http_client.send_tb_summary(config['testbed_type'])
    except Exception as e:
        #TODO: delete these
        import traceback
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)

def main():
    # load config file
    config_file = sys.argv[1]
    config = json.load(open(config_file))
    print('===== AutoGrader Testbed [%d] ===== ' % config["id"])

    connection = config['connection']

    # get HTTP server and client ready
    http_server = HTTPServer(connection['as_server'], config['required_input_files'])
    http_client = HTTPClient(
            config=connection['as_client'],
            server_listening_port=connection['as_server']['listening_port'],
    )

    # define the working order
    file_folder = os.path.join('.', 'uploads')
    backup_root_folder = os.path.join('.', 'upload_backups')

    # get hardware engine
    hardware_engine = HardwareEngineHttp(config, file_folder, backup_root_folder)
    http_server.add_hardware(hardware_engine)
    hardware_engine.add_http_client(http_client)

    # get task scheduler
    scheduler = BackgroundScheduler(standalone=True)

    # ========== LOGGING SETTINGS ==========
    #logging.basicConfig()
    print(config)
    if 'testbed_type' not in config:
        raise Exception('"testbed_type" cannot be found in configuration file')

    # schedule periodic jobs
    send_summary(http_client, config)
    scheduler.add_job(send_summary, 'interval', seconds=10,
            args=[http_client, config])
    scheduler.start()

    # start server
    http_server.start()

if __name__ == "__main__":
    main()
