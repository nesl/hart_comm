# ========== IMPORTS ==========
import json
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import AutoGrader

# ========== CONFIG FILE ==========
config_file = sys.argv[1]
config = json.load(open(config_file))
print '===== AutoGrader Testbed [%d] ===== ' % config["id"]

# ========== HTTP SERVER ==========
http_server = AutoGrader.HTTPServer(config)

# ========== HTTP CLIENT ==========
http_client = AutoGrader.HTTPClient(config)

# ========== HARDWARE ENGINE ==========
hardware = AutoGrader.HardwareEngine(config)
http_server.addHardware(hardware)
hardware.add_http_client(http_client)

# ========== TASK SCHEDULER ===========
scheduler = BackgroundScheduler()

# ========== LOGGING SETTINGS ==========
logging.basicConfig()

# send testbed summary
def send_summary():
    try:
        http_client.send_tb_summary(json.dumps(config))
    except Exception as e:
        print 'remote server is down'


# schedule periodic jobs
scheduler.add_job(send_summary, 'interval', seconds=10)
scheduler.start()

# start server
http_server.start()