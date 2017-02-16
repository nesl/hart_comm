# ========== IMPORTS ==========
import json
import sys
import signal
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import AutoGrader

# ========== CONFIG FILE ==========
config_file = sys.argv[1]
config = json.load(open(config_file))
print('===== AutoGrader Testbed [%d] ===== ' % config["id"])

# ========== HTTP SERVER ==========
http_server = AutoGrader.HTTPServer(config['connection']['as_server'], config['required_input_files'])

# ========== HTTP CLIENT ==========
http_client = AutoGrader.HTTPClient(config['connection']['as_client'])

# ========== HARDWARE ENGINE ==========
hardware_engine = AutoGrader.HardwareEngine(config)
http_server.addHardware(hardware_engine)
hardware_engine.add_http_client(http_client)

# ========== TASK SCHEDULER ===========
scheduler = BackgroundScheduler(standalone=True)

# ========== LOGGING SETTINGS ==========
logging.basicConfig()

# send testbed summary
def send_summary():
    try:
        http_client.send_tb_summary(json.dumps(config))
    except Exception as e:
        #TODO: delete these
        import traceback
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)


# schedule periodic jobs
scheduler.add_job(send_summary, 'interval', seconds=10)
scheduler.start()

# start server
http_server.start()
