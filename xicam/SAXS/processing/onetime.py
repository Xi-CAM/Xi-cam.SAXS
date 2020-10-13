import numpy as np
from dask import array as da
from typing import Tuple

import skbeam.core.correlation as corr
from xicam.core.intents import PlotIntent

from xicam.plugins.operationplugin import operation, describe_input, describe_output, visible, \
    input_names, output_names, display_name, categories, intent


@operation
@display_name('1-time Correlation')
@input_names('data', 'labels', 'number_of_buffers', 'number_of_levels')
@describe_input('data', 'Input array of two or more dimensions')
@describe_input('labels', 'Labeled array of the same shape as the image stack. \
                Each ROI is represented by sequential integers starting at one.  For \
                example, if you have four ROIs, they must be labeled 1, 2, 3, 4. \
                Background is labeled as 0')
@describe_input('num_bufs', 'Integer number of buffers. Must be even maximum \
                 lag step to compute in each generation of downsampling.')
@describe_input('num_levels', 'Integer number defining how many generations of \
                 downsampling to perform, i.e., the depth of the binomial tree \
                 of averaged frames')
@output_names('g2', 'tau')
@describe_output('g2', 'Normalized g2 data array with shape = (len(lag_steps), num_rois)')
@describe_output('tau', 'array describing tau (lag steps)')
@visible('data', False)
@visible('labels', False)
@intent(PlotIntent,
        match_key='1-time Correlation',
        name='g2',
        yLog=True,
        labels={"bottom": "&tau;", "left": "g2"},
        output_map={'x': 'tau', 'y': 'g2'})
def one_time_correlation(data: np.ndarray,
                         labels: np.ndarray,
                         num_bufs: int = 16,
                         num_levels: int = 8) -> Tuple[da.array, da.array]:
    g2, tau = corr.multi_tau_auto_corr(num_levels, num_bufs,
                                       labels.astype(np.int),
                                       np.asarray(data))
    g2 = g2.squeeze()
    return g2, tau
