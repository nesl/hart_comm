import os
import sys
import serial
import threading
import struct
import time
import traceback

from AutoGrader.devices import HardwareBase


class STM32(HardwareBase):
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
    output_metadata = None

    # thread status
    uart_reading_thread = None
    alive = True

    # execution
    execution_start_time = None

    def __init__(self, name, config, hardware_engine, file_folder):
       
        if 'baud' in config:
            self.baud_rate = config['baud']

        if "usb_path" not in config:
            raise Exception('"usb_path" field is required')
        self.usb_path = config['usb_path']

        if 'input_waveform_file' not in config:
            raise Exception('"input_waveform_file" field is required')
        self.input_waveform_path = os.path.join(file_folder, config['input_waveform_file'])

        if 'output_waveform_file' in config and config['output_waveform_file']:
            self.output_waveform_path = os.path.join(file_folder, config['output_waveform_file'])
        else:
            self.output_waveform_path = '/dev/null'

        if 'output_metadata' not in config:
            raise Exception('"output_metadata" field is required')
        self.output_metadata = config['output_metadata']

        self.name = name
        self.config = config
        self.hardware_engine = hardware_engine

    def on_before_execution(self):

        # open serial port
        tmp_dev = serial.Serial()
        tmp_dev.port = self.usb_path
        tmp_dev.baudrate = self.baud_rate
        tmp_dev.parity = serial.PARITY_NONE
        tmp_dev.bytesize = serial.EIGHTBITS
        tmp_dev.stopbits = serial.STOPBITS_ONE
        tmp_dev.timeout = 0.01
        tmp_dev.writeTimeout = None

        # open input waveform file but get rid of the metadata part
        self.fin = open(self.input_waveform_path, 'r')
        while True:
            line = self.fin.readline()
            if not line or line.strip() == '==':
                break

        # open output waveform file and write the meatadata part
        self.output_lines = []
        self.output_lines.append('')  # period
        self.output_lines.append('Tick frequency: %f' % self.output_metadata['tick_frequency'])
        self.output_lines.append('Display start')
        for pin_config in self.output_metadata['pins']:
            self.output_lines.append('%s,%s' % (
                pin_config['label'],
                ','.join(list(map(str, pin_config['indexes']))),
            ))
        self.output_lines.append('Display end')
        self.output_lines.append('==')

        self.alive = True
        
        try:
            tmp_dev.open() 
            self.dev = tmp_dev
            print('(STM32) UART is open')
            self.send_command(self.CMD_RESET_TESTER)
            print('(STM32) reset')
            time.sleep(1)
            self.uart_reading_thread = threading.Thread(
                    target=self._reading_thread, name=('STM32-%s-reading' % self.name)).start()
        except:
            exc_info = sys.exc_info()
            print('(STM32) UART device unable to open, full stack trace below')
            traceback.print_exception(*exc_info)
            self.alive = False

    def on_execute(self):
        self.execution_start_time = time.time()

        # feed input waveform file into STM32
        for line in self.fin:
            if not self.alive:
                break
            terms = line.split(',')
            pkt_type, pkt_time, pkt_val = chr(int(terms[0])), int(terms[1]), int(terms[2])
            binary = struct.pack('=ccIHc', self.START_DELIM, pkt_type.encode('ascii'), pkt_time,
                    pkt_val, self.STOP_DELIM)
            if not self.dev:
                print('(STM32) UART device does not exist, not able to send the command')
                return
            self.dev.write(binary)
            print('(STM32) packet sent', pkt_type, pkt_time, pkt_val)

        self.fin.close()

    def on_terminate(self):
        self.alive = False
        
        execution_stop_time = time.time()
        execution_elasped_time = execution_stop_time - self.execution_start_time
        self.output_lines[0] = "Period: %f" % execution_elasped_time

        with open(self.output_waveform_path, 'w') as fo:
            fo.write('\n'.join(self.output_lines))
    
    def on_reset_after_execution(self):
        
        try:
            self.dev.flush()
            self.dev.close()
            print('(STM32) UART is closed')
        except:
            print('(STM32) UART device unable to close')
        self.dev = None

    def __del__(self):
        if self.dev and self.dev.is_open:
            self.dev.close()

    def _reading_thread(self):
        rx_buffer = b''

        while self.alive:
            # continue immediately if serial isn't ready
            if not self.dev:
                continue

            # Because we set a read timeout, chances are we only get a 
            # partial of a packet
            rx_buffer += self.dev.read(self.TOTAL_PKT_LEN)
            
            # Thus, if it's not a complete packet yet, read more
            if len(rx_buffer) < self.TOTAL_PKT_LEN:
                continue

            # check the packet is valid via start and stop byte
            # (The reason that we have to use bytes[0:1] is that var[0] returns an int)
            if rx_buffer[0:1] == self.START_DELIM and rx_buffer[8:9] == self.STOP_DELIM:
                self._handle_packet_payload(rx_buffer[1:8])
            else:
                print('(STM32) bad packet!', rx_buffer[0:9])

            rx_buffer = rx_buffer[9:]
    
    def _handle_packet_payload(self, binary):
        # 1B type, 4B time, 2B val
        [pkt_type, pkt_time, pkt_val] = struct.unpack('<cLH', binary)
        try:
            pkt_type = pkt_type.decode('ascii')
        except:
            print('(STM32) Cannot handle the packet...')
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
            return
        
        print('type: %s, time: %d, val: %d' % (pkt_type, pkt_time, pkt_val))
        if pkt_type is not self.CMD_TERMINATE:
            self.output_lines.append('%d, %d, %d' % (ord(pkt_type), pkt_time, pkt_val))
        else:
            self.hardware_engine.notify_terminate()
            self.alive = False
    
    def send_command(self, cmd):
        payload = self.START_DELIM + cmd.encode() + b'\x00\x00\x00\x00\x00\x00' + self.STOP_DELIM
        self.dev.write(payload)
    
