#!/usr/bin/python

# -- imports --
import os
import re
import serial
import threading
import struct

class UARTTransceiver(threading.Thread):
    # class variables
    START_DELIM = b'S'
    STOP_DELIM = b'E'
    TOTAL_PKT_LEN = 9

    # instance variables
    baud_rate = 115200
    dev_path = None
    dev = None
    callback = None

    alive = True


    def __init__(self, baud, path, callback):
        threading.Thread.__init__(self, name="uartserial")

        self.baud_rate = baud
        self.dev_path = path
        self.callback = callback

    def __del__(self):
        if self.dev and self.dev.is_open:
            self.dev.close()
        self.alive = False

    def run(self):
        while self.alive:
            # continue immediately if serial isn't ready
            if not self.dev:
                continue

            rxBuffer = self.dev(self.TOTAL_PKT_LEN)

            # check the packet is valid via start and stop byte
            # (The reason that we have to use bytes[0:1] is that var[0] returns an int)
            if rxBuffer[0:1] == self.START_DELIM and rxBuffer[8:9] == self.STOP_DELIM:
                self.handleData(rxBuffer[1:8])

            #TODO: I think this line should be deleted
            #self.flush()

    def handleData(self, binary):
        # 1B type, 4B time, 2B val
        [pktType, pktTime, pktVal] = struct.unpack('<cLH', data_str)
        try:
            pktType = pktType.decode('ascii')
            self.callback(pktType, pktTime, pktVal)
        except:
            pass

    def open(self):
        self.dev = serial.Serial()
        self.dev.port = self.dev_path
        self.dev.baudrate = self.baud_rate
        self.dev.parity = serial.PARITY_NONE
        self.dev.bytesize = serial.EIGHTBITS
        self.dev.stopbits = serial.STOPBITS_ONE
        self.dev.timeout = 0.01
        self.dev.writeTimeout = None
        try:
            self.dev.open() 
        except:
            print('UART device unable to open')
            self.dev = None

    def close(self):
        try:
            self.dev.flush()
            self.dev.close()
        except:
            print('UART device unable to close')
        self.dev = None

    def sendCommand(self, cmd):
        payload = self.START_DELIM + cmd.encode() + b'\x00\x00\x00\x00\x00\x00' + self.STOP_DELIM
        self.dev.write(payload)

    def write(self, data):
        if not self.dev:
            print('UART device does not exist, not able to send the command')
            continue
        self.dev.write(data)

    #TODO: not sure the purpose of this method
    #def flush(self):
    #    self.dev.flushInput()
    #    self.dev.flush()

