import serial
import string
import time
import threading
import os
import shutil
import datetime
import traceback
from .UARTTransceiver import *


# output generation path
upload_root_folder_path = os.path.join('.', 'uploads')
backup_folder_path = os.path.join(upload_root_folder_path, 'backups')
outfile_path = os.path.join(upload_root_folder_path, 'output.txt')


class HardwareEngine(object):
    CMD_RESET_DUT = 'U'
    CMD_RESET_TESTER = 'R'
    CMD_ENABLE_ANALOG = 'O'
    CMD_TERMINATE = 'E'

    status = 'IDLE'
    config = None
    uart = None
    baudrate = 460800
    outfile = None
    http_client = None

    def __init__(self, config):
        # copy config JSON
        self.config = config
        # init UART transceiver
        self.uart = UARTTransceiver(self.baudrate, self.config["tester"]["path"], self.on_data_rx)

    def add_http_client(self, client):
        self.http_client = client

    def on_data_rx(self, pktType, pktTime, pktVal):
        # if termination is received, change status and close file
        print('type: %s, time: %d, val: %d' % (pktType, pktTime, pktVal))
        if pktType is not self.CMD_TERMINATE:
            self.outfile.write( '%d, %d, %d\n' % (ord(pktType), pktTime, pktVal) )
        else: # we get a terminate packet
            self.status = 'IDLE'
            print('Test complete.')
            self.outfile.close()

            # backup
            now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
            backup_dir = os.path.join(backup_folder_path, 'output', now)
            os.makedirs(backup_dir)
            shutil.copy(outfile_path, backup_dir)

            # send results file over HTTP
            try:
                self.http_client.send_waveform( outfile_path )
                print('Waveform file uploaded')
            except:
                print('Unable to upload output to server')

            # update status over HTTP
            try:
                self.http_client.send_tb_status( 'IDLE' )
                print('IDLE status sent')
            except:
                print('Unable to post status to server')

    def get_status(self):
        return self.status

    def start_test(self, wavefile_name):
        # set status to busy
        self.status = 'TESTING'
        # open output file for saving test results
        self.outfile = open(outfile_path, 'w')
        # open waveform file and give commands
        with open(wavefile_name, 'r') as wfile:
            for line in wfile:
                self.uart.sendOnePacketInCsvFormat(line)

    def reset_dut(self):
        self.uart.sendCommand( self.CMD_RESET_DUT )
        time.sleep(0.2)

    def reset_tester(self):
        self.uart.sendCommand( self.CMD_RESET_TESTER )
        
        # stop listening to UART
        self.uart.close()

        time.sleep(2.0)
        
        self.uart = UARTTransceiver(self.baudrate, self.config["tester"]["path"], self.on_data_rx)

    def enable_anlog_reading(self):
        self.uart.sendCommand( self.CMD_ENABLE_ANALOG )
