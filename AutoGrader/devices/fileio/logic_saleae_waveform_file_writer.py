import json
import re


"""
An example of the file content of Logic Saleae waveform looks like the following:

  Period: 1
  Display start
  CTL,0
  VAL,3,1
  Display end
  ==
  Time[s], Data[Hex]
  0.000000000000000, 0
  0.633994500000000, 1
  0.673993125000000, 0
  0.736037562500000, 8

Please see logic_saleae_waveform_file_reader.py for the specification of the file.
"""

class LogicSaleaeWaveformFileWriter(object):

    def __init__(self, file_path):
        # initialize instance variables
        self.file_path = file_path

        self.period_sec = None

        # display_params is a list of strings. Each string contains several comma-separated items.
        # The first item is the name of the plot, following are pin numbers.
        self.display_params = []

        # The output file path of Logic Saleae python library
        self.raw_data_path = None

    def set_period_sec(self, period_sec):
        self.period_sec = period_sec

    def add_display_param(self, plot_name, plot_pins):
        # convert a signle integer to a list
        if type(plot_pins) is int:
            plot_pins = [plot_pins]

        self.display_params.append(','.join(list(map(str, [plot_name] + plot_pins))))

    def set_raw_data_path(self, data_path):
        self.raw_data_path = data_path

    def marshal(self):
        if self.period_sec is None:
            raise Exception('"Period" is not set')
        if len(self.display_params) == 0:
            raise Exception('"Display params" is empty')
        if self.raw_data_path is None:
            raise Exception('"Raw data path" is not set')

        with open(self.raw_data_path, 'rb') as f:
            raw_waveform_data = f.read().decode()

        with open(self.file_path, 'w') as fo:
            fo.write("\n".join(
                ["Period: %f" % self.period_sec] +
                ["Display start"] +
                self.display_params +
                ["Display end"] +
                ["=="] +
                [raw_waveform_data]
            ))
