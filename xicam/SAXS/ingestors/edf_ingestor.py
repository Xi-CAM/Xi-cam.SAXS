from datetime import datetime

import fabio
import dask.array as da
import dask
import numpy as np
import mimetypes
from xicam.SAXS.ontology import NXsas
from bluesky_live.run_builder import RunBuilder
from pathlib import Path

mimetypes.add_type('application/x-edf', '.edf')


# TODO: add lazy-support
def edf_ingestor(paths):
    projections = [{'name': 'NXsas',
                    'version': '0.1.0',
                    'projection':
                        {NXsas.DATA_PROJECTION_KEY: {'type': 'linked',
                                                     'stream': 'primary',
                                                     'location': 'event',
                                                     'field': 'image'}},
                    'configuration': {}
                    }]

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
