import time

import event_model
import h5py
from dask import array as da
from pathlib import Path
from xarray import DataArray
import mimetypes

mimetypes.add_type('application/x-hdf5', '.hdf5')
I_PROJECTION_KEY = 'sasentry/sasdata/I'
QX_PROJECTION_KEY = 'sasentry/sasdata/Qx'
QY_PROJECTION_KEY = 'sasentry/sasdata/Qy'


def ingest_nxcanSAS(paths):
    assert len(paths) == 1
    path = paths[0]

    h5 = h5py.File(path, 'r')

    data = h5['sasentry']['sasdata']['I']
    Qx = h5['sasentry']['sasdata']['Qx'][()]
    Qy = h5['sasentry']['sasdata']['Qy'][()]
    axes = h5['sasentry']['sasdata'].attrs['I_axes']

    xarray = DataArray(data, dims=axes.split(','))
    dask_data = da.from_array(xarray)

    projections = [{'name': 'NXcanSAS',
                    'version': '0.1.0',
                    'projection':
                        {I_PROJECTION_KEY: {'type': 'linked',
                                                'stream': 'primary',
                                                'location': 'event',
                                                'field': 'I'},
                         QX_PROJECTION_KEY: {'type': 'linked',
                                                 'stream': 'primary',
                                                 'location': 'event',
                                                 'field': 'Qx'},
                         QY_PROJECTION_KEY: {'type': 'linked',
                                                 'stream': 'primary',
                                                 'location': 'event',
                                                 'field': 'Qy'},
                         # 'sasentry/sasdata/': {'type': 'linked',
                         #                          'stream': 'primary',
                         #                          'location': 'event',
                         #                          'field': 'g2'},
                         }

                    }]
    # Compose run start
    run_bundle = event_model.compose_run()  # type: event_model.ComposeRunBundle
    start_doc = run_bundle.start_doc
    start_doc["sample_name"] = Path(paths[0]).resolve().stem
    start_doc["projections"] = projections
    yield 'start', start_doc

    # Compose descriptor
    source = 'NXcanSAS'
    frame_data_keys = {'I': {'source': source,
                             'dtype': 'number',
                             'dims': xarray.dims,
                             # 'coords': [energy, sample_y, sample_x],
                             'shape': data.shape},
                       'Qx': {'source': source,
                              'dtype': 'number',
                              'shape': Qx.shape, },
                       'Qy': {'source': source,
                              'dtype': 'number',
                              'shape': Qy.shape, }
                       }

    frame_stream_name = 'primary'
    frame_stream_bundle = run_bundle.compose_descriptor(data_keys=frame_data_keys,
                                                        name=frame_stream_name,
                                                        # configuration=_metadata(path)
                                                        )
    yield 'descriptor', frame_stream_bundle.descriptor_doc

    # NOTE: Resource document may be meaningful in the future. For transient access it is not useful
    # # Compose resource
    # resource = run_bundle.compose_resource(root=Path(path).root, resource_path=path, spec='NCEM_DM', resource_kwargs={})
    # yield 'resource', resource.resource_doc

    # Compose datum_page
    # z_indices, t_indices = zip(*itertools.product(z_indices, t_indices))
    # datum_page_doc = resource.compose_datum_page(datum_kwargs={'index_z': list(z_indices), 'index_t': list(t_indices)})
    # datum_ids = datum_page_doc['datum_id']
    # yield 'datum_page', datum_page_doc

    yield 'event', frame_stream_bundle.compose_event(data={'I': dask_data,
                                                           'Qx': Qx,
                                                           'Qy': Qy},
                                                     timestamps={'I': time.time(),
                                                                 'Qx': time.time(),
                                                                 'Qy': time.time()})

    yield 'stop', run_bundle.compose_stop()


if __name__ == "__main__":
    path = 'test21.hdf5'

    docs = list(ingest_nxcanSAS([path]))

    print(docs)
