import mimetypes
import os
import re
from datetime import datetime
from pathlib import Path

import dask
import dask.array as da
import fabio
import numpy as np
from bluesky_live.run_builder import RunBuilder
from xicam.SAXS.ontology import NXsas

mimetypes.add_type('application/x-edf', '.edf')


def parse_txt(path):
    if not os.path.isfile(path):
        return dict()

    with open(path, 'r') as f:
        lines = f.readlines()

    paras = dict()

    # The 7.3.3 txt format is messy, with keyless values, and extra whitespaces

    keylesslines = 0
    for line in lines:
        cells = list(filter(None, re.split('[=:]+', line)))

        key = cells[0].strip()

        if cells.__len__() == 2:
            cells[1] = cells[1].split('/')[0]
            paras[key] = cells[1].strip()
        elif cells.__len__() == 1:
            keylesslines += 1
            paras['Keyless value #' + str(keylesslines)] = key

    return paras


def edf_ingestor(paths):
    # No way to know if this is reflection or transmission, so everything is reflection?
    incidence_angle = None
    detector_rotation = None
    beamline_energy = None
    detector_translate_x = None
    detector_translate_y = None

    txt_path = paths[0].replace('.edf', '.txt')
    if os.path.isfile(txt_path):
        extra_metadata = parse_txt(txt_path)

        # read incident angle
        if "Sample Alpha Stage" in extra_metadata:
            incidence_angle = np.deg2rad(float(extra_metadata["Sample Alpha Stage"]))

        detector_rotation = 0  # Assume no rotation

    projections = [{'name': 'NXsas',
                    'version': '0.1.0',
                    'projection':
                        {NXsas.DATA_PROJECTION_KEY: {'type': 'linked',
                                                     'stream': 'primary',
                                                     'location': 'event',
                                                     'field': 'image'}},
                    'configuration': {'geometry_mode': 'reflection'}
                    }]

    if incidence_angle is not None:
        projections[0]['projection'][NXsas.INCIDENCE_ANGLE_PROJECTION_KEY] = {'type': 'static',
                                                                              'value': incidence_angle}
    if detector_rotation is not None:
        projections[0]['projection'][NXsas.AZIMUTHAL_ANGLE_PROJECTION_KEY] = {'type': 'static',
                                                                              'value': detector_rotation}
    if beamline_energy is not None:
        projections[0]['projection'][NXsas.ENERGY_PROJECTION_KEY] = {'type': 'static',
                                                                     'value': beamline_energy}

    if detector_translate_x is not None:
        projections[0]['projection'][NXsas.DETECTOR_TRANSLATION_X_PROJECTION_KEY] = {'type': 'static',
                                                                                     'value': detector_translate_x}
    if detector_translate_y is not None:
        projections[0]['projection'][NXsas.DETECTOR_TRANSLATION_Y_PROJECTION_KEY] = {'type': 'static',
                                                                                     'value': detector_translate_y}

    d = []
    t = []

    lazy_read = dask.delayed(lambda path: np.flipud(fabio.open(path).data), pure=True)
    for path in paths:
        with fabio.open(path) as file:
            d.append(da.from_delayed(lazy_read(path), dtype=file.dtype, shape=file.shape))
            t.append(datetime.strptime(file.header['Date'], '%a %b  %d %H:%M:%S %Y').timestamp())

    d = np.stack(d)

    metadata = {'projections': projections, 'sample_name': Path(paths[0]).name}
    data_keys = {'image': {'source': 'Beamline 7.3.3',
                           'dtype': 'array',
                           'shape': d.shape,
                           'dims': ('dim_0', 'dim_1')}}
    with RunBuilder(metadata=metadata) as builder:
        builder.add_stream("primary",
                           data_keys=data_keys,
                           )
        builder.add_data("primary",
                         # NOTE: Put data in list, since Runbuilder.add_stream expects
                         # a sequence number to add event_page
                         data={'image': d},
                         time=t)

    builder.get_run()
    yield from builder._cache


if __name__ == '__main__':
    list(edf_ingestor(["E:\\data\\YL1031\\YL1031__2m_00000.edf"]))
