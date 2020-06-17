from xicam.plugins.operationplugin import operation, describe_input, describe_output, visible, \
                        input_names, output_names, display_name, categories, plot_hint 
import numpy as np
from skbeam.core.correlation import two_time_corr
from typing import Tuple


@operation
@display_name('1-time Correlation')
@input_names('data', 'labels', 'number_of_buffers', 'number_of_levels')
@describe_input('data', 'dimensions are: (rr, cc), iterable of 2D arrays')
@describe_input('labels', 'labeled array of the same shape as the image stack;'
                          'each ROI is represented by a distinct label (i.e., integer)')
@describe_input('num_bufs', 'maximum lag step to compute in each generation of downsampling (must be even)')
@describe_input('num_levels', 'how many generations of downsampling to perform,'
                              'i.e., the depth of the binomial tree of averaged frames default is one')
@output_names('g2', 'tau')
@describe_output('g2', 'the normalized correlation shape is (num_rois, len(lag_steps), len(lag_steps))')
@describe_output('tau', 'the times at which the correlation was computed')
@visible('data', False)
@visible('labels', False)
#TODO: check plothint
@plot_hint('tau_1', 'tau_2', name='2-time Correlation')
def two_time_correlation(data: np.ndarray,
                         labels: np.ndarray,
                         num_bufs: int = 16,
                         num_levels: int = 8) -> Tuple[np.ndarray, np.ndarray]:
    #TODO -- make composite parameter item widget to allow default (all frames) or enter value
    num_frames = len(data)
    corr = two_time_corr(labels.astype(np.int),
                         np.asarray(data),
                         num_frames,
                         num_bufs,
                         num_levels)
    g2 = corr.g2
    lag_steps = corr.lag_steps
    return g2, lag_steps


# class TwoTimeCorrelation(ProcessingPlugin):
#     labels = Input(description=('labeled array of the same shape as the image stack;'
#                                 'each ROI is represented by a distinct label (i.e., integer)'),
#                    type=np.ndarray,
#                    visible=False)
#     data = Input(description='dimensions are: (rr, cc), iterable of 2D arrays',
#                  type=np.ndarray,
#                  visible=False)
#     num_bufs = Input(description='maximum lag step to compute in each generation of downsampling (must be even)',
#                      type=int,
#                      default=16)
#     num_levels = Input(description=('how many generations of downsampling to perform, '
#                                     'i.e., the depth of the binomial tree of averaged frames default is one'),
#                        type=int,
#                        default=8)

#     g2 = Output(description='the normalized correlation shape is (num_rois, len(lag_steps), len(lag_steps))',
#                 type=np.ndarray)
#     lag_steps = Output(description='the times at which the correlation was computed',
#                        type=np.ndarray)

#     hints = [ImageHint(g2)]

#     def evaluate(self):
#         # TODO -- make composite parameter item widget to allow default (all frames) or enter value
#         num_frames = len(self.data.value)
#         corr = two_time_corr(self.labels.value.astype(np.int),
#                              np.asarray(self.data.value),
#                              num_frames,
#                              self.num_bufs.value,
#                              self.num_levels.value)
#         self.g2.value = corr.g2
#         self.lag_steps.value = corr.lag_steps

#         self.hints = [ImageHint(self.g2.value,
#                                 xlabel="&tau;<sub>1</sub>",
#                                 ylabel="&tau;<sub>2</sub>",
#                                 name="2-Time")]
