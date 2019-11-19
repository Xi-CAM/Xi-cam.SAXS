import os
import time
from pathlib import Path
from typing import Dict

import sparse
import event_model
import h5py

from xicam.core.msg import WARNING, notifyMessage, logError, logMessage
from xicam.plugins.datahandlerplugin import DataHandlerPlugin
import dask.array as da
import dask

import numpy as np


class QROI(object):
    """
    Temporary class to put the qlist into a repr-able object so all ROIs can be treated generically.
    """

    def __init__(self, q_value):
        self.q = q_value

    def __repr__(self):
        return f"q = {self.q: .3g}"


class QZReader:
    FRAME_SHIFT = 40
    PIXEL_SHIFT = 16
    PIXEL_MASK = 0xfffff
    VALUE_MASK = 0x7ff
    DET_ROWS = 512
    DET_COLS = 1024

    def __init__(self, resource_path, root, **resource_kwargs):
        # TODO sanity checks
        self.root = root
        self.resource_path = resource_path
        self.fp = open(os.path.join(root, resource_path), 'rb')
        self._num_frames = None
        self._num_bytes = None
        self.frame = 0
        self._shape = None
        self._dtype = None

    def __call__(self, **datum_kwargs):
        # return dask array on call

        return self

    def seek(self, offset=0, whence=0):
        if offset % 8:
            raise ValueError('seek value must be a multiple integer of 8')
        bytes = self.fp.seek(offset, whence)
        self.frame = None
        return bytes

    def read_buffer(self, buffer_size):
        if buffer_size is not None:
            if buffer_size % 8:
                raise ValueError('buffer size must be a multiple integer of 8')
            buf = self.read(buffer_size)
        else:
            buf = self.read()

        return buf

    def num_frames(self):
        if self._num_frames is None:
            starting_pos = self.fp.tell()

            self._num_frames = self.get_frame_at_pos(-8, os.SEEK_END) + 1

            self.seek(starting_pos)
        return self._num_frames

    def total_bytes(self):
        if self._num_bytes is None:
            starting_pos = self.fp.tell()

            self._num_bytes = self.seek(0, os.SEEK_END)

            self.fp.seek(starting_pos)
        return self._num_bytes

    def get_frame_at_pos(self, offset=0, whence=0):
        if offset:
            self.seek(offset, whence)
        buf = self.read(8)
        buf = np.frombuffer(buf, dtype='<i8')
        frames = np.right_shift(buf, self.FRAME_SHIFT)
        return frames[0]

    def read(self, *args, **kwargs):
        self.frame = None  # Invalidate frame number
        return self.fp.read(*args, **kwargs)

    def seek_to_frame(self, target):
        # TODO: these scheme assumes that each frame unit has at least one record; what if not?

        # For the simple case, short circuit
        if target == 0:
            self.seek(0)
            self.frame = 0
            return

        # First, target finding the preceding frame
        target -= 1

        # first guess is based on estimate from total number of bytes
        next_search_pos = int(target * self.bytes_per_frame() // 8 * 8)  # Always step in 8 bytes
        self.seek(next_search_pos)

        # the first seek step will be determined later by delta
        next_seek_step = 0

        # decrease step size by small factor to prevent hopping over a frame infinitely
        age = 0

        # Seek in decreasing steps until reaching target frame
        while True:
            frame_at_pos = self.get_frame_at_pos(next_seek_step, os.SEEK_CUR)
            print(frame_at_pos)
            if frame_at_pos == target:
                break
            age_factor = np.exp(-age / 10)
            next_seek_step = int(
                ((target - frame_at_pos) * self.bytes_per_frame() * age_factor) // 8 * 8)  # Always step in 8 bytes
            age += 1

        # target the following frame
        target += 1

        # Seek to beginning of frame
        while self.get_frame_at_pos() != target:
            pass

        # Seek back 8 bytes (since we just read once)
        self.seek(-8, os.SEEK_CUR)

        self.frame = target

    def bytes_per_frame(self):
        # An estimate of bytes per frame
        return self.total_bytes() / self.num_frames()

    def read_frames(self, N):
        if self.frame is None:
            raise (IndexError("Read without seeking to frame start; partial frame data would otherwise result"))

        start_frame = self.frame  # This will otherwise be invalidated by reads

        # Read 10% more than estimated to need; ideally this gets everything we want in one read; no more than .1 GB
        buffer_size = int(min(N * self.bytes_per_frame() * 1.1, .1e9) // 8 * 8)

        if buffer_size is not None:
            if buffer_size % 8:
                raise ValueError('buffer size must be a multiple integer of 8')
            buf = self.read(buffer_size)
        else:
            buf = self.read()

        buf = np.frombuffer(buf, dtype='<i8')
        frames = np.right_shift(buf, self.FRAME_SHIFT)
        pixels = np.bitwise_and(np.right_shift(buf, self.PIXEL_SHIFT), self.PIXEL_MASK)
        values = np.bitwise_and(buf, self.VALUE_MASK)

        # Trim
        trim_len = np.argmax(frames > N + start_frame - 1)
        frames = frames[:trim_len]
        pixels = pixels[:trim_len]
        values = values[:trim_len]

        rows = pixels // 1024
        cols = pixels % 1024

        return sparse.COO([frames - N, rows, cols], values, shape=(N, 512, 1024))

    def read_frame(self, N):
        self.seek_to_frame(N)
        return self.read_frames(1)

    def __getitem__(self, item):
        if isinstance(item, slice):
            if slice.step != 1:
                raise (IndexError("Slicing this data with a step size other than 1 is not supported."))

            self.seek_to_frame(slice.start)
            return self.read_frames(slice.stop - slice.start)
        elif isinstance(item, tuple):
            return self[item[0]][item[1:]]
        else:
            return self.read_frame(item)

    @property
    def shape(self):
        if self._shape is None:
            self._shape = (self.num_frames(), *self.read_frame(0).shape[-2:])
        return self._shape

    @property
    def dtype(self):
        if self._dtype is None:
            self._dtype = self.read_frame(0).dtype
        return self._dtype

    def __reduce__(self):
        return (QZReader, (self.resource_path, self.root))


"""
Handles ingestion of APS XPCS .hdf files.

Internally, these .hdf files will hold a reference to a .bin image file,
which will be loaded as well.
"""


# def __init__(self, path):
#     super(APSXPCS, self).__init__()
#     self.path = path

# def __call__(self, data_key='', slc=0, **kwargs):
#     # TODO -- change to show image data once image data is being ingested
#     h5 = h5py.File(self.path, 'r')
#     if data_key == 'norm-0-g2':
#         return h5['exchange'][data_key][:, :, slc].transpose()
#     return h5['exchange'][data_key][slc]

def ingest_aps_xpcs(paths):
    # TODO -- update for multiple paths (pending dbheader interface)
    if len(paths) > 1:
        paths = paths[0:1]
        message = 'Opening multiple already-processed data sources is not yet supported. '
        message += f'Opening the first image, {paths[0]}...'
        notifyMessage(message, level=WARNING)

    yield from _createDocument(paths)


def title(paths):
    """Returns the title of the start_doc sample_name"""
    # return the file basename w/out extension
    # TODO -- handle multiple paths
    return Path(paths[0]).resolve().stem


def _find_datasets(dataset_shape_indexes: Dict, h5: h5py.File):
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


def _createDocument(paths):
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
        datasets_and_sizes = _find_datasets(datasets_shape_indexes, h5)
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

        h5 = h5py.File(path, 'r')

        bin_file_path = h5['measurement']['instrument']['acquisition']['datafilename'].value

        # TODO -- use the processed data timestamp?
        # h5_resource = run_bundle.compose_resource(spec='QZReader',
        #                                           root=os.path.dirname(path),
        #                                           resource_path=str(bin_file_path),
        #                                           resource_kwargs={})
        # yield 'resource', h5_resource.resource_doc
        # datum = h5_resource.compose_datum(datum_kwargs={})
        # yield 'datum', datum
        #
        # yield 'event', frame_stream_bundle.compose_event(data={'frame': datum['datum_id']},
        #                                                  timestamps={'frame': timestamp})

        delayed_reader = dask.delayed(QZReader, pure=True)
        delayed_data = delayed_reader(root=os.path.dirname(bin_file_path),
                                      resource_path=os.path.basename(bin_file_path))

        # delayed_data.read_frame(2).compute()
        dtype = delayed_data.dtype.compute()
        shape = delayed_data.shape.compute()
        dask_data = da.from_delayed(delayed_data, dtype=dtype, shape=shape)

        yield 'event', frame_stream_bundle.compose_event(data={'frame': dask_data},
                                                         timestamps={'frame': timestamp})

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


if __name__ == '__main__':
    import glob

    paths = glob.glob('/home/rp/data/xpcs/APS/*.hdf')
    print(paths)

    # h5 = h5py.File(paths[0], 'r')
    # bin_file_path = h5['measurement']['instrument']['acquisition']['datafilename'].value
    # bin_file_path = '/home/rp/data/xpcs/APS/D067_Silica_att2_Rq0_00001.bin'
    # f = QZReader(root=os.path.dirname(bin_file_path), resource_path=os.path.basename(bin_file_path))
    # d = da.from_array(f)
    # f.seek_to_frame(1000)
    # data = f.read_frames(1000)
    #
    # from pyqtgraph import image, mkQApp
    # app = mkQApp()
    # i = image()
    # i.setImage(data.todense())
    # i.show()
    # app.exec_()
    # print(f.read())

    print(list(ingest_aps_xpcs(paths)))
