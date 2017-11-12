import json
import re

from serapis.utils.visualizers.fileio.waveform_query_base import WaveformQueryBase

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

The file content should consist of two sections, separated by "==" line. These two sections
are metadata section and waveform section.

The interpretation of the metadata section of the presented example is the following: The total
period of the waveform is 20 seconds. In each second, there are 5000 ticks. The display block
(surrounding by "Display start" and "Display end" lines) specifies the configuration of all the
plots, one per line. The configuration includes the plot label, and which pins are included in
this plot. In this example, two plots of waveform are going to be displayed. The first waveform
is labeled as "CTL", which captures the changes of 0th pin. The second waveform is called
"VAL", which combines the 2nd pin (the most significant) and 1st pin (the least significant).

The waveform section is composed of several lines, each line contains 3 numbers separated by
commas. These numbers are: event type, timestamp in tick, and bus value (the value of putting
all the pins in order.)

Taking the second waveform as an example, we will display 3 transitions:
  - at 0th tick, the value is 0
  - at 30000th tick, the value is 1
  - at 70000th tick, the value is 2

Or visually, it looks like the following:

  2               +-----+
                  |
  1       +-------+
          |
  0 +-----+
    0    30000   70000  100000  (tick)

"""

class STM32WaveformFileReader(WaveformQueryBase):
    ERROR_CODE_EMPTY_FILE = 1
    ERROR_CODE_NON_ASCII = 2
    ERROR_CODE_FORMAT = 3

    def __init__(self, raw_content):
        self._initialize_instance_variables()
        self._parse_raw_content(raw_content)

    def _initialize_instance_variables(self):
        self.period_sec = None
        self.tick_frequency = None

        # display_params is an array, each element is a dictionary with `name` (a string) and
        # `pins` (a list of integers)
        self.display_params = None

        # data contains a list of tuples. Each tuple contains two items, a float representing
        # start timestamp in ms, and an integer for a bus value
        self.data = None
        
        self.error_code = None

    def _parse_raw_content(self, raw_content):
        if len(raw_content) == 0:
            self.error_code = STM32WaveformFileReader.ERROR_CODE_EMPTY_FILE
            return
        
        try:
            content = raw_content.decode('ascii')
        except:
            self.error_code = STM32WaveformFileReader.ERROR_CODE_NON_ASCII
            return

        if not self._parse_content(content):
            self.error_code = STM32WaveformFileReader.ERROR_CODE_FORMAT
            return

        self.error_code = None

    def _parse_content(self, content):
        try:
            lines = content.strip().split('\n')
            num_total_lines = len(lines)
            line_idx = 0

            # E.g., Period: 20
            matches = re.search(r'^Period: *(\d+(\.\d*)?)', lines[line_idx])
            if not matches:
                return False
            self.period_sec = float(matches.group(1))
            line_idx += 1

            # E.g., Tick frequency: 5000
            matches = re.search(r'^Tick frequency: *(\d+(\.\d*)?)', lines[line_idx])
            if not matches:
                return False
            self.tick_frequency = float(matches.group(1))
            line_idx += 1

            tick_sec = 1. / self.tick_frequency

            # E.g., Display start
            #       CTL,0
            #       VAL,2,1
            #       Display end
            if not lines[line_idx].startswith('Display start'):
                return False
            line_idx += 1

            self.display_params = []  # a list of {name, pins}
            while line_idx < num_total_lines and not lines[line_idx].startswith('Display end'):
                terms = lines[line_idx].split(',')
                if len(terms) <= 1:
                    return False  # should have at least a name and a pin index
                self.display_params.append({
                    'name': terms[0],
                    'pins': [int(x) for x in terms[1:]],
                })
                line_idx += 1

            line_idx += 1

            # E.g., ==
            if not lines[line_idx].startswith('=='):
                return False
            line_idx += 1

            # E.g., 68, 0, 0
            #       68, 30000, 3
            #       68, 70000, 4
            line_terms = [l.strip().split(',') for l in lines[line_idx:]]

            # self.data a list of (start timestamp, bus value)
            self.data = [(float(l[1]) * tick_sec, int(l[2]))
                    for l in line_terms if int(l[0]) == 68]

            self.data = self._clean_waveform(self.data, self.period_sec)
        except:
            return False

        return True

    def is_successfully_parsed(self):
        return self.error_code is None

    def get_error_code(self):
        return self.error_code

    def get_error_description(self):
        if self.error_code is None:
            raise Exception("No error during parsing")

        if self.error_code == STM32WaveformFileReader.ERROR_CODE_EMPTY_FILE:
            return "Empty file"
        elif self.error_code == STM32WaveformFileReader.ERROR_CODE_NON_ASCII:
            return "Parsing error: The file includes non-ascii characters"
        elif self.error_code == STM32WaveformFileReader.ERROR_CODE_FORMAT:
            return "Parsing error: file format is not correct"
        else:
            raise Exception("Unknown error code")

    def get_period_sec(self):
        if self.error_code is not None:
            raise Exception("There is an error while parsing content")
        return self.period_sec

    def get_period_ms(self):
        if self.error_code is not None:
            raise Exception("There is an error while parsing content")
        return self.period_sec * 1000.

    def get_tick_frequency(self):
        if self.error_code is not None:
            raise Exception("There is an error while parsing content")
        return self.tick_frequency

    def get_tick_length_sec(self):
        if self.error_code is not None:
            raise Exception("There is an error while parsing content")
        return 1.0 / self.tick_frequency

    def get_tick_length_ms(self):
        if self.error_code is not None:
            raise Exception("There is an error while parsing content")
        return 1000.0 / self.tick_frequency

    def get_num_display_plots(self):
        if self.error_code is not None:
            raise Exception("There is an error while parsing content")
        return len(self.display_params)

    def get_event_series(self, series_idx, start_time_ms=None, end_time_ms=None):
        """
        When start_time_ms and/or end_time_ms is None, it is configured as default value:
        start_time_ms will be 0.0, end_time_ms will be the period length.

        Returns:
          (name, time_series)
            - name: plot name, a string
            - time_series: a list of (time_ms, bus_value). Align with both start_time_ms and
                  end_time_ms. Will filter out duplicate transitions. Timestamps are in ms.
        """

        if self.error_code is not None:
            raise Exception("There is an error while parsing content")

        start_time_sec = None if start_time_ms is None else start_time_ms / 1000.
        end_time_sec = None if end_time_ms is None else end_time_ms / 1000.

        display_param = self.display_params[series_idx]
        series_name = display_param['name']
        series_pins = display_param['pins']
        result_sec = self._get_event_series(self.data, series_pins, start_time_sec, end_time_sec)
        result_ms = [(t * 1000., v) for t, v in result_sec]
        
        return (series_name, result_ms)
