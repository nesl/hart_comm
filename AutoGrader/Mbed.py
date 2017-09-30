import os
import sys
import serial
import time
import threading
import struct
import traceback
import subprocess
import shutil

from AutoGrader.HardwareBase import HardwareBase


class Mbed(HardwareBase, threading.Thread):
    # parameters
    baud_rate = 115200
    mount_path = None
    dev_path = None
    usb_path = None
    blank_firmware_path = None
    testing_firmware_path = None
    serial_output_path = None
    log_size = 1000000

    # device info
    hardware_engine = None
    name = None
    config = None

    # serial
    dev = None
    f_serial = None
    byte_written = None

    # working threads
    alive = None
    serial_reading_thread = None
    serial_writing_thread = None

    def __init__(self, name, config, hardware_engine, file_folder):
        threading.Thread.__init__(self, name="dutserial")
        
        if 'baud' in config:
            self.baud_rate = config['baud']

        if "mount_path" not in config:
            raise Exception('"mount_path" field is required')
        self.mount_path = config['mount_path']

        if "dev_path" not in config:
            raise Exception('"dev_path" field is required')
        self.dev_path = config['dev_path']

        if "usb_path" not in config:
            raise Exception('"usb_path" field is required')
        self.dev_path = config['usb_path']

        if 'blank_firmware_path' in config:
            self.blank_firmware_path = config['blank_firmware_path']

        if 'executed_binary_source' not in config:
            raise Exception('"executed_binary_source" field is required')

        if config['executed_binary_source'] == 'hardware engine':
            if 'binary_name' not in config:
                raise Exception('"binary_name" is not provided while binary source is set to be from hardware engine')
            self.testing_firmware_path = config['binary_name']
        elif config['executed_binary_source'] == 'local file system':
            if 'binary_path' not in config:
                raise Exception('"binary_path" is not provided while binary source is set to be from local file system')
            self.testing_firmware_path = config['binary_path']
        else:
            raise Exception('Unrecognized value in "executed_binary_source" field')
            
        if 'serial_output' in config:
            self.serial_output_path = os.path.join(file_folder, config['serial_output'])
        else:
            self.serial_output_path = '/dev/null'

        if 'log_size' in config:
            self.log_size = config['log_size']

        # backup configurations
        self.hardware_engine = hardware_engine
        self.name = name
        self.config = config
        
        # take file system snapshot
        if os.getuid() != 0:
            raise Exception("FATAL: Require root permission")
        
        print("Unmounting.. (mbed name=%s) %s" % (self.name, self.dev_path))
        subprocess.call(['umount', self.dev_path])
        time.sleep(3)
        
        print("Mounting back (mbed name=%s) %s %s" % (self.name, self.dev_path, self.mount_path))
        subprocess.call(['mount', self.dev_path, self.mount_path])
        time.sleep(0.3)

    def on_before_execution(self):
        self._burn_firmware(blank_firmware_path, firmware_short_desp='blank')
        self._burn_firmware(testing_firmware_path, firmware_short_desp='testing')
        
        self.f_serial = open(self.serial_output_path, 'wb')
        self.byte_written = 0
        
        tmp_dev = serial.Serial()
        tmp_dev.port = self.usb_path
        tmp_dev.baudrate = self.baud_rate
        tmp_dev.parity = serial.PARITY_NONE
        tmp_dev.bytesize = serial.EIGHTBITS
        tmp_dev.stopbits = serial.STOPBITS_ONE
        tmp_dev.timeout = 0.01
        tmp_dev.writeTimeout = 0.0001
        
        self.alive = True

        tmp_dev.open() 
        self.dev = tmp_dev
        print('(mbed) UART is open')

        # pull obselete bytes from last session
        self.dev.reset_input_buffer()
        self.dev.reset_output_buffer()
        #for i in range(4096):  # clean up to 4K bytes
        #    print('clean', i)
        #    if not self.dev.read(1):
        #        break
        print('(mbed) Clean old bytes from the last session')

        self.serial_reading_thread = threading.Thread(target=self._read_serial,
                name=('mbed-%s' % self.name))
        self.serial_reading_thread.start()

    def on_execute(self):
        pass

    def on_terminate(self):
        self.alive = False
    
    def on_reset_after_execution(self):
        pass

    def __del__(self):
        if self.dev and self.dev.is_open:
            self.dev.close()

    def run(self):
        while self.alive:
            b = self.dev.read(1)
            if self.byte_written < self.log_size:
                self.byte_written += 1
                self.f_serial.write(b)
                self.f_serial.flush()

        try:
            self.dev.close()
            self.f_serial.close()
            print('(mbed) UART is closed')
        except:
            print('(mbed) UART device unable to close')
        self.dev = None
        self.f_serial = None

    
    def _burn_firmware(self, firmware_path, firmware_short_desp=None):
        # To make the burning process smoother, we have to copy the code to mbeds, unmound mbeds,
        # and mound mbeds. After we adapt to it, we didn't see any burning error.
        if not firmware_short_desp:
            firmware_short_desp = ''
        else:
            firmware_short_desp += ' '
        
        print("Removing old codes from mbed (name=%s)" % self.name)
        subprocess.call(['rm', '-rf', '%s/*' % self.mount_path])
        time.sleep(3)
        
        print("programming %sfirmware on mbed (name=%s)" % (firmware_short_desp, self.name))
        shutil.copy(firmware_path, self.mount_path)
        time.sleep(3)
        
        print("Unmounting.. (mbed name=%s) %s" % (self.name, self.dev_path))
        subprocess.call(['umount', self.dev_path])
        time.sleep(3)
        
        print("Mounting back (mbed name=%s) %s %s" % (self.name, self.dev_path, self.mount_path))
        subprocess.call(['mount', self.dev_path, self.mount_path])
        time.sleep(3)
    
    def _read_serial(self):
        while self.alive:
            b = self.dev.read(1)
            if not b:
                continue

            if self.byte_written < self.log_size:
                self.byte_written += 1
                self.f_serial.write(b)
                self.f_serial.flush()

        try:
            self.dev.close()
            self.f_serial.close()
            print('(mbed) UART is closed')
        except:
            print('(mbed) UART device unable to close')
        self.dev = None
        self.f_serial = None
