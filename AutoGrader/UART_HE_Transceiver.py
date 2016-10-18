import os
import re
import sys
import serial
import threading
import struct
import traceback

class UART_HE_Transceiver(threading.Thread):
    # class variables
    START_DELIM = b'S'
    STOP_DELIM = b'E'
    TOTAL_PKT_LEN = 9

    # instance variables
    baud_rate = None
    dev_path = None
    dev = None
    callback = None

    alive = True


    def __init__(self, baud, path, callback):
        threading.Thread.__init__(self, name="uartserial")

        self.baud_rate = baud
        self.dev_path = path
        self.callback = callback
        
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
            print('(HE) UART is open')
            self.start()
        except:
            print('(HE) UART device unable to open',  sys.exc_info()[0], sys.exc_info()[1])

    def __del__(self):
        if self.dev and self.dev.is_open:
            self.dev.close()

    def run(self):
        while self.alive:
            # continue immediately if serial isn't ready
            if not self.dev:
                continue

            rxBuffer = self.dev.read(self.TOTAL_PKT_LEN)
            
            if len(rxBuffer) != self.TOTAL_PKT_LEN:
                continue
            # check the packet is valid via start and stop byte
            # (The reason that we have to use bytes[0:1] is that var[0] returns an int)
            if rxBuffer[0:1] == self.START_DELIM and rxBuffer[8:9] == self.STOP_DELIM:
                self.handleData(rxBuffer[1:8])
            else:
                print('(HE) bad packet!', rxBuffer, len(rxBuffer))

        try:
            self.dev.flush()
            self.dev.close()
            print('(HE) UART is closed')
        except:
            print('(HE) UART device unable to close')
        self.dev = None

    def handleData(self, binary):
        # 1B type, 4B time, 2B val
        [pktType, pktTime, pktVal] = struct.unpack('<cLH', binary)
        try:
            pktType = pktType.decode('ascii')
            self.callback(pktType, pktTime, pktVal)
        except:
            print('(HE) Cannot handle the packet...')
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

    def close(self):
        self.alive = False

    def sendCommand(self, cmd):
        payload = self.START_DELIM + cmd.encode() + b'\x00\x00\x00\x00\x00\x00' + self.STOP_DELIM
        self.dev.write(payload)
    
    def sendOnePacketInCsvFormat(self, line):
        terms = line.split(',')
        pkt_type, pkt_time, pkt_val = chr(int(terms[0])), int(terms[1]), int(terms[2])
        binary = struct.pack('=ccIHc', self.START_DELIM, pkt_type.encode('ascii'), pkt_time, pkt_val, self.STOP_DELIM)
        self._write(binary)

    def _write(self, data):
        if not self.dev:
            print('(HE) UART device does not exist, not able to send the command')
            return
        print ('(HE) Writing to UART', data)
        self.dev.write(data)
