import os
import sys
import traceback
import shutil
import saleae

from AutoGrader.devices import HardwareBase


class LogicSaleaeWrapper(HardwareBase):
    TMP_RESULT_PATH = '/tmp/logic.csv'

    # parameters
    output_waveform_path = None

    # device info
    name = None
    config = None

    # Saleae instance
    saleae_dev = None

    def __init__(self, name, config, hardware_engine, file_folder):
        if "output_waveform_file" not in config:
            raise Exception('"output_waveform_file" field is required')
        self.output_waveform_path = os.path.join(file_folder, config['output_waveform_file'])

        self.seleae_dev = saleae.Saleae()
        if not self.seleae_dev:
            raise Exception('No Logic Seleae detected')
        active_channels_A = config['active_channels_A'] if 'active_channels_A' in config else []
        active_channels_B = config['active_channels_B'] if 'active_channels_B' in config else []
        self.seleae_dev.set_active_channels(active_channels_A, active_channels_B)

        self.name = name
        self.config = config

    def on_before_execution(self, deadline_sec):
        self.seleae_dev.set_capture_seconds(deadline_sec)

    def on_execute(self):
        self.seleae_dev.capture_start()

    def on_terminate(self):
        self.seleae_dev.capture_stop()
        self.seleae_dev.export_data2(LogicSaleaeWrapper.TMP_RESULT_PATH)
        shutil.move(LogicSaleaeWrapper.TMP_RESULT_PATH, self.output_waveform_path)
    
    def on_reset_after_execution(self):
        pass
