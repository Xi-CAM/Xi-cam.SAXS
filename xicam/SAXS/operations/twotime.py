import pyqtgraph as pg
from xicam.core import msg
from xicam.core.intents import ImageIntent
from xicam.plugins.operationplugin import operation, describe_input, describe_output, visible, \
    input_names, output_names, display_name, categories, intent
import numpy as np
from skbeam.core.correlation import two_time_corr
from typing import Tuple, Iterable

from ..patches.pyFAI import AzimuthalIntegrator
from ..utils import average_q_from_labels, get_label_array


@operation
@display_name('2-time Correlation')
# @input_names('images', 'labels', 'number_of_buffers', 'number_of_levels')
@describe_input('images', 'dimensions are: (rr, cc), iterable of 2D arrays')
@describe_input('labels', 'labeled array of the same shape as the image stack;'
                          'each ROI is represented by a distinct label (i.e., integer)')
@describe_input('num_bufs', 'maximum lag step to compute in each generation of downsampling (must be even)')
@describe_input('num_levels', 'how many generations of downsampling to perform,'
                              'i.e., the depth of the binomial tree of averaged frames default is one')
@output_names('g2', 'tau', 'qs')
@describe_output('g2', 'the normalized correlation shape is (num_rois, len(lag_steps), len(lag_steps))')
@describe_output('tau', 'the times at which the correlation was computed')
@visible('images', False)
@visible('rois', False)
@intent(ImageIntent,
        name='2-time Correlation',
        output_map={'image': 'g2', 'xvals': 'qs'},
        mixins=["AxesLabels", "XArrayView", "SliceSelector"],
        labels={"bottom": "𝜏₁", "left": "𝜏₂"})
def two_time_correlation(images: np.ndarray,
                         image_item: pg.ImageItem = None,
                         rois: Iterable[pg.ROI] = None,
                         num_bufs: int = 16,
                         num_levels: int = 8,
                         geometry: AzimuthalIntegrator = None) -> Tuple[np.ndarray, np.ndarray]:
    # TODO -- make composite parameter item widget to allow default (all frames) or enter value
    num_frames = len(images)

    labels = get_label_array(images, rois=rois, image_item=image_item)
    if labels.max() == 0:
        msg.notifyMessage("Please add an ROI over which to calculate one-time correlation.")
        raise ValueError("Please add an ROI over which to calculate one-time correlation.")

    corr = two_time_corr(labels.astype(np.int_),
                         np.asarray(images),
                         num_frames,
                         num_bufs,
                         num_levels)
    g2 = corr.g2
    lag_steps = corr.lag_steps

    # Calculate avg qs from label array for first dimension on returned g2 (so slice selector shows qs for indexing)
    qs = None
    if geometry is not None:
        qs = np.asarray(average_q_from_labels(labels, geometry))
        # qs = np.asarray([f"q={q:.3f}" for q in qs])  # FIXME: why can't we return a python list for the catalog?
        # File "xi-cam/xicam/core/execution/workflow.py", line 886, in project_intents
        #     kwargs[intent_kwarg_name] = getattr(run_catalog, operation_id).to_dask()[output_name]
        # ...
        # File "site-packages/xarray/core/dataarray.py", line 126, in _infer_coords_and_dims
        #     raise ValueError(
        #  ValueError: different number of dimensions on data and dims: 2 vs 1

    # Rotate image plane 90 degrees
    g2 = np.rot90(g2, axes=(-2, -1))

    num_labels = g2.shape[0]  # first dimension represents labels
    if not qs:
        qs = np.array(list(range(1, num_labels + 1)))
    return g2, lag_steps, qs
