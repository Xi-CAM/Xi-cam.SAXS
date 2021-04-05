import numpy as np
from dask import array as da
from typing import Tuple, List, Iterable
import pyqtgraph as pg

import skbeam.core.correlation as corr
from xicam.SAXS.patches.pyFAI import AzimuthalIntegrator
from xicam.core.intents import PlotIntent
from xicam.core import msg

from xicam.plugins.operationplugin import operation, describe_input, describe_output, visible, \
    input_names, output_names, display_name, categories, intent

from ..utils import get_label_array, average_q_from_labels


@operation
@display_name('1-time Correlation')
@input_names('images', 'rois', 'image_item', 'number_of_buffers', 'number_of_levels', )
@describe_input('images', 'Input array of two or more dimensions')
# @describe_input('labels', 'Labeled array of the same shape as the image stack. \
#                 Each ROI is represented by sequential integers starting at one.  For \
#                 example, if you have four ROIs, they must be labeled 1, 2, 3, 4. \
#                 Background is labeled as 0')
@describe_input('number_of_buffers', 'Integer number of buffers (must be even). Maximum \
                 lag step to compute in each generation of downsampling.')
@describe_input('number_of_levels', 'Integer number defining how many generations of \
                 downsampling to perform, i.e., the depth of the binomial tree \
                 of averaged frames')
@output_names('g2', 'tau', 'images', 'labels')
@describe_output('g2', 'Normalized g2 data array with shape = (len(lag_steps), num_rois)')
@describe_output('tau', 'array describing tau (lag steps)')
@visible('images', False)
@visible('rois', False)
@visible('image_item', False)
@intent(PlotIntent,
        match_key='1-time Correlation',
        name='g2',
        yLog=True,
        labels={"bottom": "𝜏", "left": "g₂"},
        output_map={'x': 'tau', 'y': 'g2'},
        mixins=["ToggleSymbols"])
def one_time_correlation(images: np.ndarray,
                         rois: Iterable[pg.ROI] = None,
                         image_item: pg.ImageItem = None,
                         num_bufs: int = 16,
                         num_levels: int = 8, ) -> Tuple[da.array, da.array, da.array, np.ndarray]:
    if images.ndim < 3:
        raise ValueError(f"Cannot compute correlation on data with {images.ndim} dimensions.")

    labels = get_label_array(images, rois=rois, image_item=image_item)
    if labels.max() == 0:
        msg.notifyMessage("Please add an ROI over which to calculate one-time correlation.")
        raise ValueError("Please add an ROI over which to calculate one-time correlation.")

    # Trim the image based on labels, and resolve to memory
    si, se = np.where(np.flipud(labels))
    trimmed_images = np.asarray(images[:, si.min():si.max() + 1, se.min():se.max() + 1])
    trimmed_labels = np.asarray(np.flipud(labels)[si.min():si.max() + 1, se.min():se.max() + 1])

    # trimmed_images[trimmed_images <= 0] = np.NaN   # may be necessary to mask values

    trimmed_images -= np.min(trimmed_images, axis=0)

    g2, tau = corr.multi_tau_auto_corr(num_levels, num_bufs,
                                       trimmed_labels.astype(np.uint8),
                                       trimmed_images)
    g2 = g2[1:].squeeze()
    # FIXME: is it required to trim the 0th value off the tau and g2 arrays?
    return g2.T, tau[1:], images, labels
