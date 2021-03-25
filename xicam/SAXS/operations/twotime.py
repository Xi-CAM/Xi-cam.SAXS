import pyqtgraph as pg
from xicam.SAXS.utils import get_label_array
from xicam.core import msg
from xicam.core.intents import ImageIntent
from xicam.plugins.operationplugin import operation, describe_input, describe_output, visible, \
    input_names, output_names, display_name, categories, intent
import numpy as np
from skbeam.core.correlation import two_time_corr
from typing import Tuple, Iterable


@operation
@display_name('2-time Correlation')
# @input_names('images', 'labels', 'number_of_buffers', 'number_of_levels')
@describe_input('images', 'dimensions are: (rr, cc), iterable of 2D arrays')
@describe_input('labels', 'labeled array of the same shape as the image stack;'
                          'each ROI is represented by a distinct label (i.e., integer)')
@describe_input('num_bufs', 'maximum lag step to compute in each generation of downsampling (must be even)')
@describe_input('num_levels', 'how many generations of downsampling to perform,'
                              'i.e., the depth of the binomial tree of averaged frames default is one')
@output_names('g2', 'tau')
@describe_output('g2', 'the normalized correlation shape is (num_rois, len(lag_steps), len(lag_steps))')
@describe_output('tau', 'the times at which the correlation was computed')
@visible('images', False)
@visible('rois', False)
@intent(ImageIntent,
        name='2-time Correlation',
        output_map={'image': 'g2'},
        mixins=["AxesLabels", "XArrayView"],
        labels={"bottom": "𝜏₁", "left": "𝜏₂"})
def two_time_correlation(images: np.ndarray,
                         image_item: pg.ImageItem = None,
                         rois: Iterable[pg.ROI] = None,
                         num_bufs: int = 16,
                         num_levels: int = 8) -> Tuple[np.ndarray, np.ndarray]:
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

#     intents = [ImageHint(g2)]

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

#         self.intents = [ImageHint(self.g2.value,
#                                 xlabel="&tau;<sub>1</sub>",
#                                 ylabel="&tau;<sub>2</sub>",
#                                 name="2-Time")]
