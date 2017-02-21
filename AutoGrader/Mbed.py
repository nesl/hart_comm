import sys
import serial
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
    name = None
    config = None

    # serial
    dev = None
    f_serial = None
    byte_written = None

    # thread status
    alive = None

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

        self.name = name
        self.config = config

    def on_before_execution(self):
        self._burn_firmware(blank_firmware_path, firmware_short_desp='blank')
        time.sleep(4.0)
        self._burn_firmware(testing_firmware_path, firmware_short_desp='testing')
        time.sleep(4.0)
        
        self.f_serial = open(self.serial_output_path, 'wb')
        self.byte_written = 0
        
        tmp_dev = serial.Serial()
        tmp_dev.port = self.usb_path
        tmp_dev.baudrate = self.baud_rate
        tmp_dev.parity = serial.PARITY_NONE
        tmp_dev.bytesize = serial.EIGHTBITS
        tmp_dev.stopbits = serial.STOPBITS_ONE
        tmp_dev.timeout = 0.01
        tmp_dev.writeTimeout = None
        
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
        pass

    def on_terminate(self):
        self.alive = False
    
    def on_reset_after_execution(self):
        #TODO: I remember we need to flush the remaining bytes, not sure where the code is
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
            print('(DUT) UART is closed')
        except:
            print('(DUT) UART device unable to close')
        self.dev = None
        self.f_serial = None

    
    def _burn_firmware(self, firmware_path, firmware_short_desp=None):
        # To make the burning process smoother, we have to copy the code to mbeds, unmound mbeds,
        # and mound mbeds. After we adapt to it, we didn't see any burning error.
        if not firmware_short_desp:
            firmware_short_desp = ''
        else:
            firmware_short_desp += ' '
        
        print("Removing old codes from DUT (name=%s)" % self.name)
        subprocess.call(['rm', '-rf', '%s/*' % self.mount_path])
        time.sleep(3)
        
        print("programming %sfirmware on DUT (name=%s)" % (firmware_short_desp, self.name))
        shutil.copy(firmware_path, self.mount_path)
        time.sleep(3)
        
        print("Unmounting.. (DUT name=%s) %s" % (self.name, self.dev_path))
        subprocess.call(['umount', self.dev_path])
        time.sleep(3)
        
        print("Mounting back (DUT name=%s) %s %s" % (self.name, self.dev_path, self.mount_path))
        subprocess.call(['mount', self.dev_path, self.mount_path])
        time.sleep(0.3)
