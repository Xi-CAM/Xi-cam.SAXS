import time
from pathlib import Path
from typing import Dict

import event_model
import h5py

from xicam.core.msg import WARNING, notifyMessage, logError, logMessage
from xicam.plugins.datahandlerplugin import DataHandlerPlugin


class APSXPCS(DataHandlerPlugin):
    """
    Handles ingestion of APS XPCS .hdf files.

    Internally, these .hdf files will hold a reference to a .bin image file,
    which will be loaded as well.
    """
    name = 'APSXPCS'
    DEFAULT_EXTENTIONS = ['.hdf', '.h5']

    def __init__(self, path):
        super(APSXPCS, self).__init__()
        self.path = path

    def __call__(self, data_key='', slc=0, **kwargs):
        # TODO -- change to show image data once image data is being ingested
        h5 = h5py.File(self.path, 'r')
        if data_key == 'norm-0-g2':
            return h5['exchange'][data_key][:,:,slc].transpose()
        return h5['exchange'][data_key][slc]

    @classmethod
    def ingest(cls, paths):
        updated_doc = dict()
        # TODO -- update for multiple paths (pending dbheader interface)
        if len(paths) > 1:
            paths = [paths[0]]
            message = 'Opening multiple already-processed data sources is not yet supported. '
            message += f'Opening the first image, {paths[0]}...'
            notifyMessage(message, level=WARNING)
            print(f'PATHS: {paths}')
        for name, doc in cls._createDocument(paths):
            if name == 'start':
                updated_doc[name] = doc
                # TODO -- should 'sample_name' and 'paths' be something different?
                doc['sample_name'] = cls.title(paths)
                doc['paths'] = paths
            if name == 'descriptor':
                if updated_doc.get('descriptors'):
                    updated_doc['descriptors'].append(doc)
                else:
                    updated_doc['descriptors'] = [doc]
            if name == 'event':
                if updated_doc.get('events'):
                    updated_doc['events'].append(doc)
                else:
                    updated_doc['events'] = [doc]
            if name == 'stop':
                updated_doc[name] = doc

        return updated_doc

    @classmethod
    def title(cls, paths):
        """Returns the title of the start_doc sample_name"""
        # return the file basename w/out extension
        # TODO -- handle multiple paths
        return Path(paths[0]).resolve().stem

    @classmethod
    def _find_datasets(cls, dataset_shape_indexes: Dict, h5: h5py.File):
        """
        Finds the HDF5 datasets based on the HDF5 paths in `dataset_shape_indexes`, and determines and stores the number
        of records for each of these datasets.

        Parameters
        ----------
        dataset_shape_indexes
            Dict with 'h5group/h5dataset' as keys and the shape index to use when determining the number of records
            in the dataset.
        h5
            The h5 file object.

        Returns
        -------
        dict
            Dictionary of the h5 dataset keys with values:
                dataset - the HDF5 dataset object
                num_items - the number of items in each dataset record

        """
        dataset_sizes = dict()
        for key, shape_index in dataset_shape_indexes.items():
            group = key.split('/')[0]
            dataset = key.split('/')[1]
            try:
                dataset_sizes[dataset] = {
                    'dataset': h5[group][dataset],
                    'num_items': [h5[group][dataset].shape[shape_index]],
                }
            except KeyError as ex:
                logMessage(f"[{key}] not found while ingesting [{h5.filename}].")
        return dataset_sizes

    @classmethod
    def _createDocument(cls, paths):
        # TODO -- add frames after being able to read in bin images
        for path in paths:
            timestamp = time.time()

            run_bundle = event_model.compose_run()
            yield 'start', run_bundle.start_doc

            source = 'APS XPCS'  # TODO -- find embedded source info?
            frame_data_keys = {'frame': {'source': source, 'dtype': 'number', 'shape': []}}
            frame_stream_name = 'primary'
            frame_stream_bundle = run_bundle.compose_descriptor(data_keys=frame_data_keys,
                                                                name=frame_stream_name)
            yield 'descriptor', frame_stream_bundle.descriptor_doc

            h5 = h5py.File(path, 'r')

            # Define the keys we want to ingest here; they don't necessarily have to exist
            datasets_shape_indexes = {
                'exchange/norm-0-g2': 0,
                'exchange/norm-0-stderr': 0,
                'exchange/tau': -1,  # tau shape is transposed
                'exchange/g2avgFIT1': 0,
                'xpcs/dqlist': 0
            }

            # Grab the HDF5 datasets and their associated sizes, size being the number of items in the dataset array
            # (e.g. grab the 'norm-0-g2' dataset,
            datasets_and_sizes = cls._find_datasets(datasets_shape_indexes, h5)
            exchange_transpose = ['norm-0-g2', 'norm-0-stderr', 'g2avgFIT1']

            reduced_data_keys = dict()
            for dataset in datasets_and_sizes:
                try:
                    reduced_data_keys[dataset] = {
                        'source': source,
                        'dtype': 'number',
                        'shape': datasets_and_sizes[dataset]['num_items'],
                    }
                except Exception as ex:
                    logError(ex)

            result_stream_name = '1-Time'
            reduced_stream_bundle = run_bundle.compose_descriptor(data_keys=reduced_data_keys,
                                                                  name=result_stream_name)
            yield 'descriptor', reduced_stream_bundle.descriptor_doc

            frames = []
            # TODO -- use the processed data timestamp?
            for frame in frames:
                yield 'event', frame_stream_bundle.compose_event(data={'frame', frame},
                                                                 timestamps={'frame', timestamp})


            # Define datasets that are the same for all events (not zipped)
            # e.g. the same tau dataset is used for all of the events
            consistent_datasets = ['tau']
            # Grab the actual arrays from each dataset, transposing so that the first dimension of the array
            # represents the number of dataset items. (e.g. norm-0-g2 might be stored in the dataset as an array
            # of shape (50, 3), which represents 3 g2 curves, with each g2 curve containing 50 points; so, we want
            # to transpose that for zipping)
            array_data = dict()
            for name, dataset in datasets_and_sizes.items():
                if name not in consistent_datasets:
                    if name in exchange_transpose:
                        array_data[name] = dataset['dataset'][()].squeeze().T
                    else:
                        array_data[name] = dataset['dataset'][()].squeeze()

            # Zip according to the dataset arrays' first dimensions (grab each 'curve' from the array of curves)
            for zipped in zip(*array_data.values()):

                # Compose a new dictionary with the dataset keys and the zipped dataset item (e.g. 'curve')
                data = dict(zip(array_data.keys(), zipped))
                data['dqlist'] = QROI(data['dqlist'])
                for dataset_key in consistent_datasets:
                    data[dataset_key] = datasets_and_sizes[dataset_key]['dataset'][()].squeeze()
                timestamps = dict(zip(data.keys(), len(data.keys()) * [timestamp]))
                yield 'event', reduced_stream_bundle.compose_event(data=data, timestamps=timestamps)

            yield 'stop', run_bundle.compose_stop()


class QROI(object):
    """
    Temporary class to put the qlist into a repr-able object so all ROIs can be treated generically.
    """
    def __init__(self, q_value):
        self.q = q_value

    def __repr__(self):
        return f"q = {self.q: .3g}"
