import json
import sys
import signal
import logging
import os

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
    
    # define the working order
    file_folder = os.path.join('.', 'solo_test_folder')

    # check input files are present, and output files do not exist
    for input_file in config['required_input_files']:
        input_file_path = os.path.join(file_folder, input_file)
        if not os.path.isfile(input_file_path):
            raise Exception("Cannot find input file \"%s\"" % input_file_path)
    for output_file in config['required_output_files']:
        output_file_path = os.path.join(file_folder, output_file)
        if os.path.isfile(output_file_path):
            os.remove(output_file_path)

    # get hardware engine and test
    hardware_engine = HardwareEngine(config, file_folder)
    hardware_engine.grade_task(execution_time_sec)

if __name__ == "__main__":
    main()
