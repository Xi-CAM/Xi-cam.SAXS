from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import fabio
import uuid
import re
import functools
from pathlib import Path


class EDFPlugin(DataHandlerPlugin):
    name = 'EDFPlugin'

    DEFAULT_EXTENTIONS = ['.edf']

    descriptor_keys = ['ByteOrder', 'HeaderID', 'VersionNumber', 'Dim_1', 'Dim_2', 'count_time', 'object_keys']

    def __call__(self, path, *args, **kwargs):
        return fabio.open(path).data

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseTXTFile(path):
        p = Path(path)
        if not p.suffix == '.txt':
            path = str(p.with_suffix('.txt'))

        if not os.path.isfile(path):
            return dict()

        with open(path, 'r') as f:
            lines = f.readlines()

        paras = dict()

        # The 7.3.3 txt format is messy, with keyless values, and extra whitespaces

        keylesslines = 0
        for line in lines:
            cells = [_f for _f in re.split('[=:]+', line) if _f]

            key = cells[0].strip()

            if cells.__len__() == 2:
                cells[1] = cells[1].split('/')[0]
                paras[key] = key_cast(key, cells[1].strip())
            elif cells.__len__() == 1:
                keylesslines += 1
                paras['Keyless value #' + str(keylesslines)] = key

        return paras

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(path):
        md = fabio.open(path).header
        md.update({'object_keys': {'pilatus2M': ['primary']}})
        return md


def key_cast(key, value):
    return conversions[key_type_map.get(key, 'str')](value)


_ALS_KEY_MAP = {
    'ABS(Vertical Beam Position)': 'event',
    'AI Channel 6': 'event',
    'AI Channel 7': 'event',
    'AIs': 'event',
    'AO Waveform': 'event',
    'Alpha_scan_I0_intensities': 'event',
    'Alpha_scan_I1_intensities': 'event',
    'Alpha_scan_diode_intensities': 'event',
    'Alpha_scan_positions': 'event',
    'Beam Current Over Threshold': 'event',
    'Beam Current': 'event',
    'Beamline Pass Beam AI': 'event',
    'Beamline Pass Beam': 'event',
    'Beamline Shutter AI': 'event',
    'Beamline Shutter Closed': 'event',
    'Beamline Shutter Open': 'event',
    'Beamstop X': 'event',
    'Beamstop Y': 'event',
    'Bruker pulses': 'event',
    'ByteOrder': ['start', 'event'],
    'DIOs': 'event',
    'DataType': ['start', 'event'],
    'Date': ['start', 'event'],
    'Detector Horizontal': 'event',
    'Detector Left Motor': 'event',
    'Detector Right Motor': 'event',
    'Detector Vertical': 'event',
    'Dim_1': ['descriptor', 'event'],
    'Dim_2': ['descriptor', 'event'],
    'EZ fast tension stage': 'event',
    'Exit Slit bottom': 'event',
    'Exit Slit left': 'event',
    'Exit Slit right': 'event',
    'Exit Slit top': 'event',
    'Feedback Interlock': 'event',
    'Flight Tube Horizontal': 'event',
    'Flight Tube Vertical': 'event',
    'GIWAXS beamstop X': 'event',
    'GIWAXS beamstop Y thorlabs': 'event',
    'GIWAXS beamstop Y': 'event',
    'Gate Shutter': 'event',
    'Gate': 'event',
    'GiSAXS Beamstop Counter': 'event',
    'GiSAXS Beamstop': 'event',
    'Hacked Ager Stage': 'event',
    'HeaderID': ['start', 'event'],
    'I1 AI': 'event',
    'I1': 'event',
    'Image': ['event', 'event'],
    'Izero AI': 'event',
    'Izero': 'event',
    'Keyless value #1': 'event',
    'Keyless value #2': 'event',
    'Keyless value #3': 'event',
    'Kramer strain data': 'event',
    'M1 Alignment Tune': 'event',
    'M1 Bend': 'event',
    'M1 Pitch': 'event',
    'M201 Feedback': 'event',
    'Mono Angle': 'event',
    'Motorized Lab Jack': 'event',
    'Motorized Lab Jack1': 'event',
    'Motors': 'event',
    'PCO Invert': 'event',
    'PHI Alignment Beamstop': 'event',
    'Pilatus 100K exp out': 'event',
    'Pilatus 1M Trigger Pulse': 'event',
    'Pilatus 300KW trigger pulse': 'event',
    'Printing motor': 'event',
    'SAXS Protector': 'event',
    'Sample Alpha Stage': 'event',
    'Sample Phi Stage': 'event',
    'Sample Rotation Stage ESP': 'event',
    'Sample Rotation Stage Miller': 'event',
    'Sample Rotation Stage': 'event',
    'Sample Thickness Stage': 'event',
    'Sample X Stage Fine': 'event',
    'Sample X Stage': 'event',
    'Sample Y Stage Arthur': 'event',
    'Sample Y Stage': 'event',
    'Sample Y Stage_old': 'event',
    'Size': ['descriptor', 'event'],
    'Slit 1 in Position': 'event',
    'Slit 2 in Position': 'event',
    'Slit Bottom Good': 'event',
    'Slit Top Good': 'event',
    'Slit1 bottom': 'event',
    'Slit1 left': 'event',
    'Slit1 right': 'event',
    'Slit1 top': 'event',
    'Sum of Slit Current': 'event',
    'Temp Beamline Shutter Open': 'event',
    'VersionNumber': ['start', 'event'],
    'Vertical Beam Position': 'event',
    'Xtal2 Pico 1 Feedback': 'event',
    'Xtal2 Pico 1': 'event',
    'Xtal2 Pico 2 Feedback': 'event',
    'Xtal2 Pico 2': 'event',
    'Xtal2 Pico 3 Feedback': 'event',
    'Xtal2 Pico 3': 'event',
    'count_time': ['descriptor', 'event'],
    'run': ['event', 'event'],
    'slit1 bottom current': 'event',
    'slit1 top current': 'event',
    'title': ['event', 'event'],
}

key_type_map = {'HeaderID': 'str',
                'Image': 'int',
                'VersionNumber': 'str',
                'ByteOrder': 'str',
                'DataType': 'str',
                'Dim_1': 'int',
                'Dim_2': 'int',
                'Size': 'int',
                'Date': 'date',
                'count_time': 'float',
                'title': 'str',
                'run': 'int',
                'Keyless value #1': 'float',
                'Keyless value #2': 'float',
                'Keyless value #3': 'float',
                'Motors': 'int',
                'Sample X Stage': 'float',
                'Sample Y Stage': 'float',
                'Sample Thickness Stage': 'float',
                'Sample X Stage Fine': 'float',
                'Sample Alpha Stage': 'float',
                'Sample Phi Stage': 'float',
                'M201 Feedback': 'float',
                'M1 Pitch': 'float',
                'Sample Rotation Stage': 'float',
                'M1 Bend': 'float',
                'Detector Horizontal': 'float',
                'Detector Vertical': 'float',
                'Slit1 top': 'float',
                'Slit1 bottom': 'float',
                'Slit1 right': 'float',
                'Slit1 left': 'float',
                'Exit Slit top': 'float',
                'Exit Slit bottom': 'float',
                'Exit Slit left': 'float',
                'Exit Slit right': 'float',
                'GIWAXS beamstop X': 'float',
                'GIWAXS beamstop Y': 'float',
                'Beamstop X': 'float',
                'Beamstop Y': 'float',
                'Detector Right Motor': 'float',
                'Detector Left Motor': 'float',
                'Motorized Lab Jack': 'float',
                'M1 Alignment Tune': 'float',
                'EZ fast tension stage': 'float',
                'Motorized Lab Jack1': 'float',
                'Sample Rotation Stage ESP': 'float',
                'Printing motor': 'float',
                'GIWAXS beamstop Y thorlabs': 'float',
                'Sample Y Stage Arthur': 'float',
                'Flight Tube Horizontal': 'float',
                'Flight Tube Vertical': 'float',
                'Hacked Ager Stage': 'float',
                'Sample Rotation Stage Miller': 'float',
                'Mono Angle': 'float',
                'Xtal2 Pico 1 Feedback': 'float',
                'Xtal2 Pico 2 Feedback': 'float',
                'Xtal2 Pico 3 Feedback': 'float',
                'Xtal2 Pico 1': 'float',
                'Xtal2 Pico 2': 'float',
                'Xtal2 Pico 3': 'float',
                'Sample Y Stage_old': 'float',
                'AO Waveform': 'float',
                'DIOs': 'int',
                'SAXS Protector': 'float',
                'Beamline Shutter Closed': 'float',
                'Beam Current Over Threshold': 'float',
                'Slit 1 in Position': 'float',
                'Slit 2 in Position': 'float',
                'Temp Beamline Shutter Open': 'float',
                'Beamline Shutter Open': 'float',
                'Feedback Interlock': 'float',
                'Beamline Pass Beam': 'float',
                'Gate Shutter': 'float',
                'Bruker pulses': 'float',
                'Slit Top Good': 'float',
                'Slit Bottom Good': 'float',
                'AIs': 'int',
                'Beam Current': 'float',
                'Beamline Shutter AI': 'float',
                'Beamline Pass Beam AI': 'float',
                'slit1 bottom current': 'float',
                'slit1 top current': 'float',
                'GiSAXS Beamstop': 'float',
                'Izero AI': 'float',
                'I1 AI': 'float',
                'PHI Alignment Beamstop': 'float',
                'AI Channel 6': 'float',
                'AI Channel 7': 'float',
                'Vertical Beam Position': 'float',
                'Pilatus 1M Trigger Pulse': 'float',
                'Pilatus 300KW trigger pulse': 'float',
                'PCO Invert': 'float',
                'Gate': 'float',
                'Izero': 'float',
                'I1': 'float',
                'GiSAXS Beamstop Counter': 'float',
                'Sum of Slit Current': 'float',
                'Pilatus 100K exp out': 'float',
                'Kramer strain data': 'float',
                'ABS(Vertical Beam Position)': 'float',
                'Alpha_scan_positions': 'tabdelimitedfloat',
                'Alpha_scan_I0_intensities': 'tabdelimitedfloat',
                'Alpha_scan_I1_intensities': 'tabdelimitedfloat',
                'Alpha_scan_diode_intensities': 'tabdelimitedfloat'
                }

conversions = {'int': lambda x: int(x.strip()),
               'float': lambda x: float(x.strip()),
               'str': lambda x: x.strip(),
               'date': lambda x: x.strip(),
               'tabdelimitedfloat': lambda x: list(map(float, x.split('\t'))) if x else []}


def _data_keys_from_value(v, src_name, object_name):
    kind_map = {'i': 'integer',
                'f': 'number',
                'U': 'string',
                'S': 'string'}
    return {'dtype': kind_map[np.array([v]).dtype.kind],
            'shape': [],
            'source': src_name,
            'object_name': object_name}


def _gen_descriptor_from_dict(ev_data, src_name):
    data_keys = {}
    confiuration = {}
    obj_keys = {}

    for k, v in ev_data.items():
        data_keys[k] = _data_keys_from_value(v, src_name, k)
        obj_keys[k] = [k]
        confiuration[k] = {'data': {},
                           'data_keys': {},
                           'timestamps': {}}

    return {'data_keys': data_keys,
            'time': time.time(),
            'uid': str(uuid.uuid4()),
            'configuration': confiuration,
            'object_keys': obj_keys}
