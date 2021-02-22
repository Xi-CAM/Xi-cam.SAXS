import fabio
import mimetypes
import time
from xicam.SAXS.ontology import NXsas
from xarray import DataArray
import dask.array as da


from bluesky_live.run_builder import RunBuilder

mimetypes.add_type('application/x-edf', '.edf')


# TODO: add lazy-support
def edf_ingestor(paths):
    projections = [{'name': 'NXSAS',
                    'version': '0.1.0',
                    'projection':
                        {NXsas.DATA_PROJECTION_KEY: {'type': 'linked',
                                               'stream': 'primary',
                                               'location': 'event',
                                               'field': 'image'}},
                    'configuration': {}
                    }]

    data = None
    d = None
    with fabio.open(paths[0]) as file:
        d = file.data
        data = DataArray(d)

    metadata = {'projections': projections}
    data_keys = {'image': {'source': 'Beamline 7.3.3',
                           'dtype': 'array',
                           'shape': data.shape,
                           # 'shape': (3,),
                           'dims': data.dims,}}
    with RunBuilder(metadata=metadata) as builder:
        builder.add_stream("primary",
                           data={'image': data},
                           # data={'image': [1,2,3]},
                           data_keys=data_keys,
                           )


    builder.get_run()
    yield from builder._cache
