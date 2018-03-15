import numpy as np
from xicam.plugins import ProcessingPlugin, Input, InOut
from scipy.ndimage import morphology


class ThresholdMaskPlugin(ProcessingPlugin):
    name = 'Threshold Mask'

    data = Input(description='Frame image data',
                 type=np.ndarray)
    minimum = Input(description='Threshold floor',
                    type=int,
                    default=3)
    maximum = Input(description='Threshold ceiling',
                    type=int,
                    default=1e10)
    neighborhood = Input(description='Neighborhood size in pixels for morphological opening. Only clusters of this size'
                                     ' that fail the threshold are masked',
                         type=int,
                         default=2)
    mask = InOut(description='Thresholded mask (1 is masked)',
                 type=np.ndarray)

    def evaluate(self):
        mask = np.logical_or(self.data.value < self.minimum.value, self.data.value > self.maximum.value)

        y, x = np.ogrid[-self.neighborhood.value:self.neighborhood.value + 1,
               -self.neighborhood.value:self.neighborhood.value + 1]
        kernel = x ** 2 + y ** 2 <= self.neighborhood.value ** 2

        morphology.binary_opening(mask, kernel, output=mask)  # write-back to mask
        if self.mask.value is not None:
            mask = np.logical_or(mask, self.mask.value)  # .astype(np.int, copy=False)
        self.mask.value = mask
