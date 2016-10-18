import serial
import string
import time
import threading
import os
import shutil
import datetime
import traceback

from .UART_HE_Transceiver import *
from .UART_DUT_Transceiver import *


# output generation path
upload_root_folder_path = os.path.join('.', 'uploads')
backup_folder_path = os.path.join(upload_root_folder_path, 'backups')
outfile_path = os.path.join(upload_root_folder_path, 'output.txt')
log_path = os.path.join(upload_root_folder_path, 'dut_uart.binary')


class HardwareEngine(object):
    CMD_RESET_DUT = 'U'
    CMD_RESET_TESTER = 'R'
    CMD_ENABLE_ANALOG = 'O'
    CMD_TERMINATE = 'E'

    status = 'IDLE'
    config = None
    he_uart = None
    he_baudrate = 460800
    dut_uart = None
    dut_baudrate = 46800
    outfile = None
    http_client = None

    def __init__(self, config):
        # copy config JSON
        self.config = config
        # init UART transceiver
        self.he_uart = UART_HE_Transceiver(self.he_baudrate, self.config["tester"]["path"], self.on_he_data_rx)

    def add_http_client(self, client):
        self.http_client = client

    def on_he_data_rx(self, pktType, pktTime, pktVal):
        # if termination is received, change status and close file
        print('type: %s, time: %d, val: %d' % (pktType, pktTime, pktVal))
        if pktType is not self.CMD_TERMINATE:
            self.outfile.write( '%d, %d, %d\n' % (ord(pktType), pktTime, pktVal) )
        else: # we get a terminate packet
            self.status = 'IDLE'
            print('Test complete.')

            # Stop getting result from HE. We cannot close HE UART for now as any other command
            # packet can come. Close the file to ensure no further result packet is logged
            self.outfile.close()

            # Stop getting result from DUT. Just need to close entire DUT communication
            self.dut_uart.close()
            self.dut_uart = None

            # backup
            now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
            
            backup_output_dir = os.path.join(backup_folder_path, 'output', now)
            os.makedirs(backup_output_dir)
            shutil.copy(outfile_path, backup_output_dir)
            
            backup_log_dir = os.path.join(backup_folder_path, 'log', now)
            os.makedirs(backup_log_dir)
            shutil.copy(log_path, backup_log_dir)
            
            # send results file over HTTP
            if self.http_client.send_dut_output(outfile_path, log_path):
                print('Waveform file uploaded')
            else:
                print('Unable to upload output to server')

            # update status over HTTP
            if self.http_client.send_tb_status(self.status):
                print('IDLE status sent')
            else:
                print('Unable to post status to server')

    def get_status(self):
        return self.status

    def start_test(self, wavefile_name):
        # set status to busy
        self.status = 'TESTING'

        # open output file for saving test results; open dut serial communication for log files
        self.outfile = open(outfile_path, 'w')

        #TODO: should not assume there is only one DUT
        self.dut_uart = UART_DUT_Transceiver(self.dut_baudrate, self.config["duts"][0]["usb_path"], log_path)
        
        # open waveform file and give commands
        with open(wavefile_name, 'r') as wfile:
            for line in wfile:
                self.he_uart.sendOnePacketInCsvFormat(line)

    def reset_dut(self):
        # Make sure DUT hang up UARTs. Things can happen if a testing session
        # is on going, or the E-packet is missing so that the session never ends.
        if self.dut_uart:
            self.dut_uart.close()
            self.dut_uart = None

        self.he_uart.sendCommand(self.CMD_RESET_DUT)

        # give it some time to recover
        time.sleep(0.2)

    def reset_hardware_engine(self):
        self.he_uart.sendCommand(self.CMD_RESET_TESTER)
        
        # stop listening to UART
        self.he_uart.close()

        # give it some time for hardware engine to recover from reset.
        # TODO: anytime beyond 0.5 is too long
        time.sleep(2.0)
        
        self.he_uart = UART_HE_Transceiver(self.he_baudrate, self.config["tester"]["path"], self.on_he_data_rx)

    def enable_anlog_reading(self):
        self.he_uart.sendCommand(self.CMD_ENABLE_ANALOG)
