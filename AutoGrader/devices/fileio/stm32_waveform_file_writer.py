import json
import re


"""
An example of the file content of STM32 waveform looks like the following:

  Period: 20
  Tick frequency: 5000
  Display start
  CTL,0
  VAL,2,1
  Display end
  ==
  68, 0, 0
  68, 30000, 3
  68, 70000, 4

Please see stm32_waveform_file_reader.py for the specification of the file.
"""

class STM32WaveformFileWriter(object):

    def __init__(self, file_path):
        # initialize instance variables
        self.file_path = file_path

        self.period_ms = None
        self.tick_frequency = None

        # display_params is a list of strings. Each string contains several comma-separated items.
        # The first item is the name of the plot, following are pin numbers.
        self.display_params = []

        # data contains a list of strings. Each string contains 3 comman-separated integers, which
        # are packet code, timestamp in tick, and a bus value
        self.data = []

    def set_period_sec(self, period_sec):
        self.period_ms = period_sec * 1000.

    def set_period_ms(self, period_ms):
        self.period_ms = period_ms

    def set_tick_frequency(self, frequency):
        self.tick_frequency = frequency

    def add_display_param(self, plot_name, plot_pins):
        # convert a signle integer to a list
        if type(plot_pins) is int:
            plot_pins = [plot_pins]

        self.display_params.append(','.join(list(map(str, [plot_name] + plot_pins))))

    def add_event(self, event_code, time, bus_value):
        self.data.append('%d,%d,%d' % (event_code, time, bus_value))

    def marshal(self):
        if self.period_ms is None:
            raise Exception('"Period" is not set')
        if self.tick_frequency is None:
            raise Exception('"Tick frequency" is not set')
        if len(self.display_params) == 0:
            raise Exception('"Display params" is empty')

        with open(self.file_path, 'w') as fo:
            fo.write("\n".join(
                ["Period: %f" % (self.period_ms / 1000.)] +
                ["Tick frequency: %f" % self.tick_frequency] +
                ["Display start"] +
                self.display_params +
                ["Display end"] +
                ["=="] +
                self.data
            ))
