import serial
import string
import time
import threading
import os
import shutil
import datetime
import traceback
import importlib

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
    STATUS_IDLE = "IDLE"
    STATUS_BUSY = "TESTING"

    status = STATUS_IDLE
    config = None

    hardware_dict = None
    hardware_init_order = None

    def __init__(self, config):
        self.config = config
        hardware_dict = config['hardware_list']

        # get hardware initialization order
        if not 'hardware_init_order' in config:
            self.hardware_init_order = []
            for hardware_name in config['hardware_list']:
                self.hardware_init_order.append(hardware_name)
        else:
            self.hardware_init_order = config['hardware_init_order']
            if len(self.hardware_init_order) != len(config['hardware_list']):
                raise Exception('hardware_list and hardware_init_order do not match in configuration file')
            for hardware_name in self.hardware_init_order:
                if hardware_name not in config['hardware_list']:
                    raise Exception('hardware_list and hardware_init_order do not match in configuration file')

        self.hardware_dict = {}
        for hardware_name in config['hardware_list']:
            hardware_config = config['hardware_list'][hardware_name]
            init_params = hardware_config['init_params']
            module_name, class_name = hardware_config['class'].rsplit(".", 1)
            MyClass = getattr(importlib.import_module(module_name), class_name)
            instance = MyClass(hardware_name, init_params, self)
            self.hardware_dict[hardware_name] = instance

    def add_http_client(self, client):
        self.http_client = client

    def on_he_data_rx(self, pktType, pktTime, pktVal):
        # if termination is received, change status and close file
        print('type: %s, time: %d, val: %d' % (pktType, pktTime, pktVal))
        if pktType is not self.CMD_TERMINATE:
            self.dummy_out_waveform_file.write('%d, %d, %d\n' % (ord(pktType), pktTime, pktVal) )
        else: # we get a terminate packet
            self.status = STATUS_IDLE
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
        self.status = STATUS_TESTING

        # open output file for saving test results; open dut serial communication for log files
        self.dummy_out_waveform_file = open(dummy_out_waveform_path, 'w')

        self.dut1_uart = UART_DUT_Transceiver(
                self.dut1_baudrate, self.dut_configs[1]["usb_path"], dut1_serial_path)
        self.dut2_uart = UART_DUT_Transceiver(
                self.dut2_baudrate, self.dut_configs[2]["usb_path"], dut2_serial_path)
        self.dut3_uart = UART_DUT_Transceiver(
                self.dut3_baudrate, self.dut_configs[3]["usb_path"], dut3_serial_path)
        

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
    
    def notify_terminate(self):
        #TODO: notify all hardware terminate
        pass
        
    def request_grade_assignment(self, input_files, secret_code):
        """
        Return:
          True if succesfully storing the data
        """
        #TODO: store input files somewhere
        #TODO: update status
        #TODO: create a new thread to start the grading thing
        return True
