import numpy as np
import skbeam.core.correlation as corr

from xicam.plugins.hints import PlotHint
from xicam.plugins.processingplugin import Input, Output, ProcessingPlugin


class OneTimeCorrelation(ProcessingPlugin):
    data = Input(description='Array of two or more dimensions.', type=np.ndarray, visible=False)

    labels = Input(description='''Labeled array of the same shape as the image stack.
        Each ROI is represented by sequential integers starting at one.  For
        example, if you have four ROIs, they must be labeled 1, 2, 3,
        4. Background is labeled as 0''',
                   type=np.ndarray,
                   visible=False)
    # Set to num_levels to 1 if multi-tau correlation isn't desired,
    # then set num_bufs to number of images you wish to correlate
    num_levels = Input(description='''How many generations of downsampling to perform, i.e., the depth of
        the binomial tree of averaged frames''',
                       type=int,
                       default=1,
                       name='number of levels')
    num_bufs = Input(description='must be even maximum lag step to compute in each generation of downsampling',
                     type=int,
                     default=1000,
                     name='number of buffers')

    g2 = Output(name='norm-0-g2',
                description='the normalized correlation shape is (len(lag_steps), num_rois)',
                type=np.ndarray)
    lag_steps = Output(name='tau',
                       type=np.ndarray)

    def evaluate(self):
        self.g2.value, self.lag_steps.value = corr.multi_tau_auto_corr(self.num_levels.value,
                                                                       self.num_bufs.value,
                                                                       self.labels.value.astype(np.int),
                                                                       np.asarray(self.data.value))
        self.g2.value = self.g2.value.squeeze()
        self.hints = [PlotHint(self.lag_steps, self.g2, name="1-Time")]
