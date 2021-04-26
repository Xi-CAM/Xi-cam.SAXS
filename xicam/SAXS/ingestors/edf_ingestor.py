import fabio
import mimetypes
from xicam.SAXS.ontology import NXsas
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

    with fabio.open(paths[0]) as file:
        d = file.data

    metadata = {'projections': projections}
    data_keys = {'image': {'source': 'Beamline 7.3.3',
                           'dtype': 'array',
                           'shape': d.shape,
                           'dims': ('dim_0', 'dim_1')}}
    with RunBuilder(metadata=metadata) as builder:
        builder.add_stream("primary",
                           #NOTE: Put data in list, since Runbuilder.add_stream expects
                           #a sequence number to add event_page
                           data={'image': [d]},
                           data_keys=data_keys,
                           )

    builder.get_run()
    yield from builder._cache
