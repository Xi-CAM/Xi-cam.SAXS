import fabio
import mimetypes

from bluesky_live.run_builder import RunBuilder

mimetypes.add_type('application/x-edf', '.edf')
DATA_PROJECTION_KEY = "/entry/instrument/detector/data"


# TODO: add lazy-support
def edf_ingestor(paths):
    projections = [{'name': 'NXSAS',
                    'version': '0.1.0',
                    'projection':
                        {DATA_PROJECTION_KEY: {'type': 'linked',
                                               'stream': 'primary',
                                               'location': 'event',
                                               'field': 'image'}},
                    'configuration': {'ask': 'Dylan'}  # FIXME: ask Dylan. do we need this in all our other projections?
                    }]

    data = None
    with fabio.open(paths[0]) as file:
        data = file.data

    metadata = {'projections': projections}
    with RunBuilder(metadata=metadata) as builder:
        builder.add_stream("primary",
                           data={'image': data})
                           # data_keys={'image': {'source': 'Beamline 7.3.3',
                           #                      'dtype': 'array',
                           #                      'shape': data.shape}})

    builder.get_run()
    yield from builder._cache
