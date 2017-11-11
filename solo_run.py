import json
import sys
import signal
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from AutoGrader import HardwareEngine
from AutoGrader.http import HTTPServer, HTTPClient


def main():
    try:
        config_file = sys.argv[1]
        execution_time_sec = int(sys.argv[2])
    except:
        print('Error: bad arguments')
        print('')
        print('Usage: ./%s config_file execution_time_sec' % sys.argv[0])
    
    # load config file
    config = json.load(open(config_file))
    print('++++++ AutoGrader Solo Version Testbed [%d] ++++++' % config["id"])

    # get hardware engine and test
    hardware_engine = HardwareEngine(config)
    hardware_engine.grade_task(execution_time_sec)

if __name__ == "__main__":
    main()
