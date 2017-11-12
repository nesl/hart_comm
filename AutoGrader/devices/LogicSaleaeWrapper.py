import sys
import traceback
import shutil
import os
import time

import saleae

from AutoGrader.devices import HardwareBase
from AutoGrader.devices.fileio.logic_saleae_waveform_file_writer import LogicSaleaeWaveformFileWriter

class LogicSaleaeWrapper(HardwareBase):
    """
    Before testbed is running, make sure start Logic Saleae GUI first
    """

    TMP_OUTPUT_PATH = '/tmp/logic.csv'

    def __init__(self, name, config, hardware_engine, file_folder):
        
        # parameters
        self.output_waveform_path = None

        # device info
        self.name = None
        self.config = None

        # Saleae instance
        self.saleae_dev = None

        # execution info
        self.execution_start_time = None

        # parse config
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

    def on_before_execution(self):
        self.seleae_dev.set_capture_seconds(300) # test for maximum 5 minutes
        self.execution_start_time = time.time()

    def on_execute(self):
        self.seleae_dev.capture_start()

    def on_terminate(self):
        self.seleae_dev.capture_stop()
        self.seleae_dev.export_data2(LogicSaleaeWrapper.TMP_OUTPUT_PATH)

        execution_time = time.time() - self.execution_start_time
        
        writer = LogicSaleaeWaveformFileWriter(self.output_waveform_path)
        writer.set_period_sec(execution_time)
        
        for pin_set in self.config['output_metadata']['pins']:
            writer.add_display_param(
                    plot_name=pin_set['label'],
                    plot_pins=pin_set['indexes'],
            )
        
        writer.set_raw_data_path(LogicSaleaeWrapper.TMP_OUTPUT_PATH)
        writer.marshal()
    
    def on_reset_after_execution(self):
        pass
