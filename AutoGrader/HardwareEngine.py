import serial
import string
import time
import threading
import os
import shutil
import datetime
import traceback
import saleae

from .UART_HE_Transceiver import *
from .UART_DUT_Transceiver import *


# output generation path
upload_root_folder_path = os.path.join('.', 'uploads')
backup_folder_path = os.path.join(upload_root_folder_path, 'backups')
dummy_out_waveform_path = os.path.join(upload_root_folder_path, 'dummy_out_waveform')
output_waveform_path = os.path.join(upload_root_folder_path, 'output_waveform')
dut1_serial_path = os.path.join(upload_root_folder_path, 'dut1_serial')
dut2_serial_path = os.path.join(upload_root_folder_path, 'dut2_serial')
dut3_serial_path = os.path.join(upload_root_folder_path, 'dut3_serial')


class HardwareEngine(object):
    CMD_RESET_DUT = 'U'
    CMD_RESET_TESTER = 'R'
    CMD_ENABLE_ANALOG = 'O'
    CMD_TERMINATE = 'E'

    status = 'IDLE'
    config = None
    
    he_uart = None
    he_baudrate = 460800
    dummy_out_waveform_file = None
    
    dut1_uart = None
    dut1_baudrate = 115200

    dut2_uart = None
    dut2_baudrate = 115200

    dut3_uart = None
    dut3_baudrate = 115200

    seleae_dev = None

    http_client = None
    dut_configs = None  # a shorthand to access dut-related configs

    def __init__(self, config):
        # copy config JSON
        self.config = config
        self.dut_configs = {}
        for d in self.config["duts"]:
            self.dut_configs[ d["id"] ] = d

        # init UART transceiver
        self.he_uart = UART_HE_Transceiver(
                self.he_baudrate, self.config["tester"]["path"], self.on_he_data_rx)

        # get logic saleae instance
        self.seleae_dev = saleae.Saleae()
        if not self.seleae_dev:
            raise Exception('No Logic Seleae detected')
        self.seleae_dev.set_active_channels([0,1,2,3], [])
        self.seleae_dev.set_capture_seconds(130)

    def add_http_client(self, client):
        self.http_client = client

    def on_he_data_rx(self, pktType, pktTime, pktVal):
        # if termination is received, change status and close file
        print('type: %s, time: %d, val: %d' % (pktType, pktTime, pktVal))
        if pktType is not self.CMD_TERMINATE:
            self.dummy_out_waveform_file.write('%d, %d, %d\n' % (ord(pktType), pktTime, pktVal) )
        else: # we get a terminate packet
            self.status = 'IDLE'
            print('Test complete.')

            # Stop getting result from HE. We cannot close HE UART for now as any other command
            # packet can come. Close the file to ensure no further result packet is logged
            self.dummy_out_waveform_file.close()

            # Stop getting result from DUT. Just need to close entire DUT communication
            self.dut1_uart.close()
            self.dut1_uart = None
            self.dut2_uart.close()
            self.dut2_uart = None
            self.dut3_uart.close()
            self.dut3_uart = None
            self.seleae_dev.capture_stop()
            self.seleae_dev.export_data2('/tmp/logic.csv')
            shutil.copy('/tmp/logic.csv', output_waveform_path)

            # backup
            now = datetime.datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
            
            backup_output_dir = os.path.join(backup_folder_path, 'output', now)
            os.makedirs(backup_output_dir)
            shutil.copy(output_waveform_path, backup_output_dir)
            shutil.copy(dut1_serial_path, backup_output_dir)
            shutil.copy(dut2_serial_path, backup_output_dir)
            shutil.copy(dut3_serial_path, backup_output_dir)
            
            # send results file over HTTP
            output_files = {
                'file_output_waveform': output_waveform_path,
                'file_dut1_serial': dut1_serial_path,
                'file_dut2_serial': dut2_serial_path,
                'file_byte_exchange_report': dut3_serial_path,
            }
            if self.http_client.send_dut_output(output_files):
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
        self.dummy_out_waveform_file = open(dummy_out_waveform_path, 'w')

        self.dut1_uart = UART_DUT_Transceiver(
                self.dut1_baudrate, self.dut_configs[1]["usb_path"], dut1_serial_path)
        self.dut2_uart = UART_DUT_Transceiver(
                self.dut2_baudrate, self.dut_configs[2]["usb_path"], dut2_serial_path)
        self.dut3_uart = UART_DUT_Transceiver(
                self.dut3_baudrate, self.dut_configs[3]["usb_path"], dut3_serial_path)
        
        self.seleae_dev.capture_start()

        # open waveform file and give commands
        with open(wavefile_name, 'r') as wfile:
            for line in wfile:
                self.he_uart.sendOnePacketInCsvFormat(line)

    def reset_dut(self):
        # Make sure DUT hang up UARTs. Things can happen if a testing session
        # is on going, or the E-packet is missing so that the session never ends.
        if self.dut1_uart:
            self.dut1_uart.close()
            self.dut1_uart = None
        if self.dut2_uart:
            self.dut2_uart.close()
            self.dut2_uart = None
        if self.dut3_uart:
            self.dut3_uart.close()
            self.dut3_uart = None

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
        
        self.he_uart = UART_HE_Transceiver(self.he_baudrate,
                self.config["tester"]["path"], self.on_he_data_rx)

    def enable_anlog_reading(self):
        self.he_uart.sendCommand(self.CMD_ENABLE_ANALOG)

