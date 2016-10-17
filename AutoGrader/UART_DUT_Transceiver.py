import os
import re
import sys
import serial
import threading
import struct
import traceback

class UARTTransceiver(threading.Thread):
    # instance variables
    baud_rate = None
    dev_path = None
    dev = None
    f_log = None
    byte_written = None
    log_size = None

    alive = True

    def __init__(self, baud, dev_path, log_path, log_size=1000000):
        threading.Thread.__init__(self, name="dutserial")

        self.baud_rate = baud
        self.dev_path = dev_path
        self.f_log = open(log_path, 'w')
        self.byte_written = 0
        self.log_size = log_size
        
        tmp_dev = serial.Serial()
        tmp_dev.port = self.dev_path
        tmp_dev.baudrate = self.baud_rate
        tmp_dev.parity = serial.PARITY_NONE
        tmp_dev.bytesize = serial.EIGHTBITS
        tmp_dev.stopbits = serial.STOPBITS_ONE
        tmp_dev.timeout = 0.01
        tmp_dev.writeTimeout = None
        try:
            tmp_dev.open() 
            self.dev = tmp_dev
            print('(DUT) UART is open')
            self.start()
        except:
            print('(DUT) UART device unable to open',  sys.exc_info()[0], sys.exc_info()[1])
            f_log.close()
            is_alive = False

    def __del__(self):
        if self.dev and self.dev.is_open:
            self.dev.close()

    def run(self):
        while self.alive:
            b = self.dev.read(1)
            if self.byte_written < self.log_size:
                self.byte_written += 1
                self.f_log.write(b)

        try:
            self.dev.close()
            self.f_log.close()
            print('(DUT) UART is closed')
        except:
            print('(DUT) UART device unable to close')
        self.dev = None
        self.f_log = None

    def close(self):
        self.alive = False
