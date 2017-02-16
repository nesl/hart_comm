import sys
import serial
import threading
import struct
import traceback
import subprocess
import shutil


class STM32(HardwareBase, threading.Thread):
    CMD_RESET_DUT = 'U'
    CMD_RESET_TESTER = 'R'
    CMD_ENABLE_ANALOG = 'O'
    CMD_TERMINATE = 'E'
    
    START_DELIM = b'S'
    STOP_DELIM = b'E'
    TOTAL_PKT_LEN = 9

    # parameters
    baud_rate = 460800
    usb_path = None
    input_waveform_path = None
    output_waveform_path = None

    # device info
    name = None
    config = None

    # parent
    hardware_engine = None

    # serial
    dev = None

    # files
    fin = None
    fout = None

    # thread status
    alive = True

    def __init__(self, name, config, hardware_engine):
        threading.Thread.__init__(self, name="dutserial")
        
        if 'baud' in config:
            self.baud_rate = config['baud']

        if "usb_path" not in config:
            raise Exception('"usb_path" field is required')
        self.dev_path = config['usb_path']

        if not 'input_waveform_file' in config:
            raise Exception('"input_waveform_file" field is required')
        self.input_waveform_path = config['input_waveform_file']

        if 'output_waveform_file' in config and config['output_waveform_file']:
            self.output_waveform_path = config['input_waveform_file']
        else:
            self.output_waveform_path = '/dev/null'

        self.name = name
        self.config = config
        self.hardware_engine = hardware_engine

    def on_before_execution(self):
        self.f_serial = open(self.serial_output_path, 'wb')
        
        tmp_dev = serial.Serial()
        tmp_dev.port = self.usb_path
        tmp_dev.baudrate = self.baud_rate
        tmp_dev.parity = serial.PARITY_NONE
        tmp_dev.bytesize = serial.EIGHTBITS
        tmp_dev.stopbits = serial.STOPBITS_ONE
        tmp_dev.timeout = 0.01
        tmp_dev.writeTimeout = None

        # open waveform file and give commands
        fin = open(input_wavefile_path, 'r')
        fout = open(output_waveform_path, 'w')

        self.alive = True
        
        try:
            tmp_dev.open() 
            self.dev = tmp_dev
            print('(DUT) UART is open')
            self.start()
        except:
            print('(DUT) UART device unable to open',  sys.exc_info()[0], sys.exc_info()[1])
            self.f_serial.close()
            self.alive = False

    def on_execute(self):
        for line in self.fin:
            self.sendOnePacketInCsvFormat(line)
            terms = line.split(',')
            pkt_type, pkt_time, pkt_val = chr(int(terms[0])), int(terms[1]), int(terms[2])
            binary = struct.pack('=ccIHc', self.START_DELIM, pkt_type.encode('ascii'), pkt_time, pkt_val, self.STOP_DELIM)
            if not self.dev:
                print('(HE) UART device does not exist, not able to send the command')
                return
            print ('(HE) Writing to UART', data)
            #TODO: need a lock for the serial.
            #TODO: have to check is it still alive or not
            self.dev.write(data)

    def on_terminate(self):
        self.alive = False
    
    def on_reset_after_execution(self):
        #TODO: I remember we need to flush the remaining bytes, not sure where the code is
        pass

    def __del__(self):
        if self.dev and self.dev.is_open:
            self.dev.close()

    def run(self):
        rx_buffer = b''

        while self.alive:
            # continue immediately if serial isn't ready
            if not self.dev:
                continue

            # Because we set a read timeout, chances are we only get a 
            # partial of a packet
            #TODO: need a lock for the serial.
            rx_buffer += self.dev.read(self.TOTAL_PKT_LEN)
            
            # Thus, if it's not a complete packet yet, read more
            if len(rx_buffer) < self.TOTAL_PKT_LEN:
                continue

            # check the packet is valid via start and stop byte
            # (The reason that we have to use bytes[0:1] is that var[0] returns an int)
            if rx_buffer[0:1] == self.START_DELIM and rx_buffer[8:9] == self.STOP_DELIM:
                self._handle_packet_payload(rx_buffer[1:8])
            else:
                print('(HE) bad packet!', rx_buffer[0:9])

            rx_buffer = rx_buffer[9:]

        try:
            self.dev.flush()
            self.dev.close()
            print('(HE) UART is closed')
        except:
            print('(HE) UART device unable to close')
        self.dev = None
    
    def _handle_packet_payload(self, binary):
        # 1B type, 4B time, 2B val
        [pkt_type, pkt_time, pkt_val] = struct.unpack('<cLH', binary)
        try:
            pkt_type = pkt_type.decode('ascii')
            self.callback(pkt_type, pkt_time, pkt_val)
        except:
            print('(HE) Cannot handle the packet...')
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        
        print('type: %s, time: %d, val: %d' % (pkt_type, pkt_time, pkt_val))
        if pkt_type is not self.CMD_TERMINATE:
            self.fout.write('%d, %d, %d\n' % (ord(pkt_type), pkt_time, pkt_val))
        else:
            self.hardware_engine.notify_terminate()
            self.alive = False
