import os
import sys
import serial
import threading
import struct
import traceback
import subprocess
import shutil
import time

from AutoGrader.devices import HardwareBase


class Mbed_SupplyFloatingNumber(HardwareBase, threading.Thread):
    # parameters
    baud_rate = 115200
    mount_path = None
    dev_path = None
    usb_path = None
    blank_firmware_path = None
    testing_firmware_path = None
    floating_file_path = None
    serial_output_path = None

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

    # device snapshots
    existing_ttys = None

    # input info
    num_samples = None
    input_bytes = None
    sending_events = None
    expected_received_bytes = None

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
        self.usb_path = config['usb_path']

        if 'blank_firmware_path' in config:
            self.blank_firmware_path = config['blank_firmware_path']

        if 'executed_binary_source' not in config:
            raise Exception('"executed_binary_source" field is required')
        
        if config['executed_binary_source'] == 'hardware engine':
            if 'binary_name' not in config:
                raise Exception('"binary_name" is not provided while binary source is set to be from hardware engine')
            self.testing_firmware_path = os.path.join(file_folder, config['binary_name'])
        elif config['executed_binary_source'] == 'local file system':
            if 'binary_path' not in config:
                raise Exception('"binary_path" is not provided while binary source is set to be from local file system')
            self.testing_firmware_path = config['binary_path']
        else:
            raise Exception('Unrecognized value in "executed_binary_source" field')
        
        if 'floating_input_file' not in config:
            raise Exception('"floating_input_file" field is required')
        self.floating_file_path = os.path.join(file_folder, config['floating_input_file'])

        if 'serial_output' in config:
            self.serial_output_path = os.path.join(file_folder, config['serial_output'])
        else:
            self.serial_output_path = '/dev/null'

        # backup configurations
        self.hardware_engine = hardware_engine
        self.name = name
        self.config = config

        # take file system snapshot
        if os.getuid() != 0:
            raise Exception("FATAL: Require root permission")

        #self.existing_ttys = self._device_folder_snapshot()
        
        print("Unmounting.. (DUT name=%s) %s" % (self.name, self.dev_path))
        subprocess.call(['umount', self.dev_path])
        time.sleep(3)
        
        print("Mounting back (DUT name=%s) %s %s" % (self.name, self.dev_path, self.mount_path))
        subprocess.call(['mount', self.dev_path, self.mount_path])
        time.sleep(0.3)

    def on_before_execution(self):
        # prepare the input
        with open(self.floating_file_path) as f:
            self.num_samples = int(f.readline().strip())
            self.input_bytes = b''
            for i in range(self.num_samples):
                x, y, z = tuple(map(float, f.readline().strip().split(' ')))
                self.input_bytes += struct.pack('=fff', x, y, z)
            num_sending_events = int(f.readline().strip())
            self.sending_events = []
            for i in range(num_sending_events):
                terms = f.readline().strip().split(' ')
                num_bytes, waiting_time = int(terms[0]), float(terms[1])
                self.sending_events.append((num_bytes, waiting_time))
        self.expected_received_bytes = (((self.num_samples // 100) * 21) + 3) * 4

        # configure the mbed
        time.sleep(4.0)

        #self.dev_path = self._get_dev_path()
        #self.usb_path = self._get_usb_path()
        print('dev path', self.dev_path)
        print('mount path', self.mount_path)

        self._burn_firmware(self.blank_firmware_path, firmware_short_desp='blank')
        self._burn_firmware(self.testing_firmware_path, firmware_short_desp='testing')
        
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
        print('(DUT) UART is open')

        # pull obselete bytes from last session
        for i in range(4096):  # clean up to 4K bytes
            print('clean', i)
            if not self.dev.read(1):
                break
        print('(DUT) Clean old bytes from the last session')

        self.serial_reading_thread = threading.Thread(target=self._read_serial,
                name=('DUT-%s' % self.name))
        self.serial_reading_thread.start()

    def on_execute(self):
        print('(DUT) on execute')
        bidx = 0
        print('(DUT) on execute, %d events' % len(self.sending_events))
        for chunk_size, wait_time in self.sending_events:
            for i in range(chunk_size):
                if not self.alive:
                    return
                #print('(DUT) surely going to send chunk_size=%d, wait_time=%.3f' % (chunk_size, wait_time))
                try:
                    self.dev.write(self.input_bytes[bidx:bidx+1])
                except:
                    pass

                #print(self.dev.write(self.input_bytes[bidx:bidx+1]))
                bidx += 1
                #print('(DUT) send %d/%d' % (bidx, len(self.input_bytes)))
            print('(DUT) send %d/%d' % (bidx, len(self.input_bytes)))
            time.sleep(wait_time)

    def on_terminate(self):
        self.alive = False
    
    def __del__(self):
        if self.dev and self.dev.is_open:
            self.dev.close()

    def _read_serial(self):
        while self.alive:
            b = self.dev.read(1)
            if not b:
                continue

            if self.byte_written < self.expected_received_bytes:
                self.byte_written += 1
                #if self.byte_written % 1 == 0:
                print('(DUT) %d/%d written bytes' % (self.byte_written, self.expected_received_bytes), self.byte_written == self.expected_received_bytes)
                self.f_serial.write(b)
                self.f_serial.flush()
                if self.byte_written == self.expected_received_bytes:
                    self.hardware_engine.notify_terminate()

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
        time.sleep(3)

    def _device_folder_snapshot(self):
        process = subprocess.Popen(['ls', '/dev/'], stdout=subprocess.PIPE)
        (output, _) = process.communicate()
        return output.decode().strip().split('\n')

    def _get_dev_path(self):
        process = subprocess.Popen(['df', '-h'], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        (output, err) = process.communicate()

        if err:
            raise Exception('FATAL: df command shows something is wrong')
    
        line = output.decode().strip().split('\n')[-1]
        terms = line.split(' ')
        dev_path = terms[0]
        if not dev_path.startswith('/dev/sd'):
            raise Exception('FATAL: Cannot find the device path')
        return dev_path

    def _get_usb_path(self):
        process = subprocess.Popen(['ls', '/dev/'], stdout=subprocess.PIPE)
        (output, _) = process.communicate()
        for line in output.decode().strip().split('\n'):
            if line.startswith('ttyACM') and line not in self.existing_ttys:
                return os.path.join('/dev/', line)
